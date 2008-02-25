# -*- coding: utf-8 -*-
"""
    sphinx.highlighting
    ~~~~~~~~~~~~~~~~~~~

    Highlight code blocks using Pygments.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import sys
import cgi
import re
import parser

try:
    import pygments
    from pygments import highlight
    from pygments.lexers import PythonLexer, PythonConsoleLexer, CLexer, \
         TextLexer, RstLexer
    from pygments.formatters import HtmlFormatter, LatexFormatter
    from pygments.filters import ErrorToken
    from pygments.style import Style
    from pygments.styles import get_style_by_name
    from pygments.styles.friendly import FriendlyStyle
    from pygments.token import Generic, Comment, Number
except ImportError:
    pygments = None
else:
    class SphinxStyle(Style):
        """
        Like friendly, but a bit darker to enhance contrast on the green
        background.
        """

        background_color = '#eeffcc'
        default_style = ''

        styles = FriendlyStyle.styles
        styles.update({
            Generic.Output: '#333',
            Comment: 'italic #408090',
            Number: '#208050',
        })

    lexers = dict(
        none = TextLexer(),
        python = PythonLexer(),
        pycon = PythonConsoleLexer(),
        rest = RstLexer(),
        c = CLexer(),
    )
    for _lexer in lexers.values():
        _lexer.add_filter('raiseonerror')



def escape_tex(text):
    return text.replace('@', '\x00').    \
                replace('[', '\x01').    \
                replace(']', '\x02').    \
                replace('\x00', '@at[]').\
                replace('\x01', '@lb[]').\
                replace('\x02', '@rb[]')


class PygmentsBridge(object):
    def __init__(self, dest='html', stylename='sphinx'):
        if not pygments:
            return
        self.dest = dest
        if stylename == 'sphinx':
            style = SphinxStyle
        else:
            style = get_style_by_name(stylename)
        self.hfmter = HtmlFormatter(style=style)
        self.lfmter = LatexFormatter(style=style)

    def highlight_block(self, source, lang):
        def unhighlighted():
            if self.dest == 'html':
                return '<pre>' + cgi.escape(source) + '</pre>\n'
            else:
                return '\\begin{Verbatim}[commandchars=@\\[\\]]\n' + \
                       escape_tex(source) + '\\end{Verbatim}\n'
        if not pygments:
            return unhighlighted()
        if lang == 'python':
            if source.startswith('>>>'):
                # interactive session
                lexer = lexers['pycon']
            else:
                # maybe Python -- try parsing it
                src = source + '\n'

                # Replace "..." by a special mark, which is also a valid python expression
                # (Note, the highlighter gets the original source, this is only done
                #  to allow "..." in code and still highlight it as Python code.)
                mark = "__highlighting__ellipsis__"
                src = src.replace("...", mark)

                # lines beginning with "..." are probably placeholders for suite
                src = re.sub(r"(?m)^(\s*)" + mark + "(.)", r"\1"+ mark + r"# \2", src)

                # if we're using 2.5, use the with statement
                if sys.version_info >= (2, 5):
                    src = 'from __future__ import with_statement\n' + src

                try:
                    parser.suite(src)
                except (SyntaxError, UnicodeEncodeError):
                    return unhighlighted()
                else:
                    lexer = lexers['python']
        else:
            lexer = lexers[lang]
        try:
            return highlight(source, lexer, self.dest == 'html' and self.hfmter or self.lfmter)
        except ErrorToken:
            # this is most probably not the selected language, so let it pass unhighlighted
            return unhighlighted()

    def get_stylesheet(self):
        if not pygments:
            return ''
        return (self.dest == 'html' and self.hfmter or self.lfmter).get_style_defs()
