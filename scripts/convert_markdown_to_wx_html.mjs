#!/usr/bin/env node

import fs from 'node:fs/promises';
import process from 'node:process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

function loadMarked() {
  try {
    const modPath = require.resolve('marked', { paths: [process.cwd()] });
    const mod = require(modPath);
    return mod.marked || mod;
  } catch (error) {
    throw new Error(
      '未找到 marked 依赖。请在当前项目执行: pnpm add marked (或 npm i marked)'
    );
  }
}

const marked = loadMarked();

const FONT_SERIF = "Optima-Regular, Optima, PingFangSC-light, PingFangTC-light, 'PingFang SC', Cambria, Cochin, Georgia, Times, 'Times New Roman', serif";
const FONT_SANS = "Roboto, Oxygen, Ubuntu, Cantarell, PingFangSC-light, PingFangTC-light, 'Open Sans', 'Helvetica Neue', sans-serif";
const MONO_FONT = 'Operator Mono, Consolas, Monaco, Menlo, monospace';

const DEFAULT_THEME = {
  BASE: {
    'text-align': 'left',
    color: '#3f3f3f',
    'line-height': '1.5',
    'font-size': '16px',
  },
  BASE_BLOCK: {
    margin: '20px 10px',
  },
  block: {
    h2: {
      'font-size': '140%',
      'text-align': 'center',
      'font-weight': 'normal',
      margin: '80px 10px 40px 10px',
    },
    h3: {
      'font-weight': 'bold',
      'font-size': '120%',
      margin: '40px 10px 20px 10px',
    },
    p: {
      margin: '10px 10px',
      'line-height': '1.6',
    },
    blockquote: {
      color: 'rgb(91, 91, 91)',
      padding: '1px 0 1px 10px',
      background: 'rgba(158, 158, 158, 0.1)',
      'border-left': '3px solid rgb(158,158,158)',
    },
    code: {
      'font-size': '80%',
      overflow: 'auto',
      color: '#333',
      background: 'rgb(247, 247, 247)',
      'border-radius': '2px',
      padding: '10px',
      'line-height': '1.3',
      border: '1px solid rgb(236,236,236)',
      margin: '20px 0',
    },
    image: {
      'border-radius': '4px',
      display: 'block',
      margin: '20px auto',
      width: '100%',
    },
    image_org: {
      'border-radius': '4px',
      display: 'block',
    },
    ol: {
      'margin-left': '0',
      'padding-left': '20px',
    },
    ul: {
      'margin-left': '0',
      'padding-left': '20px',
      'list-style': 'circle',
    },
    footnotes: {
      margin: '10px 10px',
      'font-size': '14px',
    },
  },
  inline: {
    listitem: {
      'text-indent': '-20px',
      display: 'block',
      margin: '10px 10px',
    },
    codespan: {
      'font-size': '90%',
      color: '#ff3502',
      background: '#f8f5ec',
      padding: '3px 5px',
      'border-radius': '2px',
    },
    link: {
      color: 'rgb(13, 117, 252)',
    },
    strong: {},
    table: {
      'border-collapse': 'collapse',
      margin: '20px 0',
    },
    thead: {
      background: 'rgba(0,0,0,0.05)',
    },
    td: {
      'font-size': '80%',
      border: '1px solid #dfdfdf',
      padding: '4px 8px',
    },
    footnote: {
      'font-size': '12px',
    },
  },
};

function copy(base, extend) {
  return Object.assign({}, base, extend);
}

function buildStyleToken(style) {
  return 'style="' + Object.entries(style).map(([k, v]) => `${k}:${v}`).join(';') + '"';
}

function buildTheme(theme, fonts) {
  const mapping = {};
  const base = copy(theme.BASE, { 'font-family': fonts });
  const baseBlock = copy(base, { margin: '20px 10px' });

  for (const [ele, style] of Object.entries(theme.inline)) {
    const merged = copy(style, ele === 'codespan' ? { 'font-family': MONO_FONT } : {});
    mapping[ele] = copy(base, merged);
  }

  for (const [ele, style] of Object.entries(theme.block)) {
    const merged = copy(style, ele === 'code' ? { 'font-family': MONO_FONT } : {});
    mapping[ele] = copy(baseBlock, merged);
  }

  return mapping;
}

export function convertMarkdownToWxHtml(markdown, options = {}) {
  const useReferences = true;
  const stetchImage = true;
  const fonts = options.fonts || FONT_SERIF;
  const theme = options.theme || DEFAULT_THEME;
  const styleMap = buildTheme(theme, fonts);

  let footnotes = [];
  let footnoteIndex = 0;

  function s(token) {
    return buildStyleToken(styleMap[token] || {});
  }

  function addFootnote(title, link) {
    footnoteIndex += 1;
    footnotes.push([footnoteIndex, title, link]);
    return footnoteIndex;
  }

  const renderer = new marked.Renderer();

  renderer.heading = (text, level) => {
    return level < 3
      ? `<h2 ${s('h2')}>${text}</h2>`
      : `<h3 ${s('h3')}>${text}</h3>`;
  };

  renderer.paragraph = (text) => `<p ${s('p')}>${text}</p>`;
  renderer.blockquote = (text) => `<blockquote ${s('blockquote')}>${text}</blockquote>`;

  renderer.code = (text, infostring) => {
    let escaped = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const lines = escaped.split('\n');
    const codeLines = [];
    const numbers = [];
    for (const line of lines) {
      codeLines.push(`<code><span class="code-snippet_outer">${line || '<br>'}</span></code>`);
      numbers.push('<li></li>');
    }
    const lang = infostring || '';
    return '<section class="code-snippet__fix code-snippet__js">'
      + '<ul class="code-snippet__line-index code-snippet__js">' + numbers.join('') + '</ul>'
      + '<pre class="code-snippet__js" data-lang="' + lang + '">' + codeLines.join('') + '</pre>'
      + '</section>';
  };

  renderer.codespan = (text) => `<code ${s('codespan')}>${text}</code>`;

  renderer.listitem = (text) => {
    return '<span ' + s('listitem') + '><span style="margin-right: 10px;"><%s/></span>' + text + '</span>';
  };

  renderer.list = (text, ordered) => {
    const segments = text.split('<%s/>');
    if (!ordered) {
      return '<p ' + s('ul') + '>' + segments.join('•') + '</p>';
    }
    let body = segments[0];
    for (let i = 1; i < segments.length; i += 1) {
      body += i + '.' + segments[i];
    }
    return '<p ' + s('ol') + '>' + body + '</p>';
  };

  renderer.image = (href, title, text) => {
    return '<img ' + s(stetchImage ? 'image' : 'image_org')
      + ' src="' + href + '" title="' + (title || '') + '" alt="' + (text || '') + '"/>';
  };

  renderer.link = (href, title, text) => {
    if (href && href.indexOf('https://mp.weixin.qq.com') === 0) {
      return '<a href="' + href + '" title="' + (title || text) + '">' + text + '</a>';
    }

    if (useReferences) {
      const ref = addFootnote(title || text, href || '');
      return '<span ' + s('link') + '>' + text + '<sup>[' + ref + ']</sup></span>';
    }

    return '<a href="' + href + '" title="' + (title || text) + '" ' + s('link') + '>' + text + '</a>';
  };

  renderer.strong = renderer.em = (text) => `<strong ${s('strong')}>${text}</strong>`;
  renderer.table = (header, body) => `<table ${s('table')}><thead ${s('thead')}>${header}</thead><tbody>${body}</tbody></table>`;
  renderer.tablecell = (text) => `<td ${s('td')}>${text}</td>`;

  let output = marked(markdown || '', { renderer });

  if (footnotes.length > 0) {
    const footnoteArray = footnotes.map(([idx, title, link]) => {
      if (title === link) {
        return `<code style="font-size: 90%; opacity: 0.6;">[${idx}]</code>: <i>${title}</i><br/>`;
      }
      return `<code style="font-size: 90%; opacity: 0.6;">[${idx}]</code> ${title}: <i>${link}</i><br/>`;
    });
    output += '<h3 ' + s('h3') + '>References</h3><p ' + s('footnotes') + '>' + footnoteArray.join('\n') + '</p>';
  }

  return output;
}

function parseArgs(argv) {
  const args = {
    input: '',
    output: '',
    font: 'serif',
  };

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--input') args.input = argv[i + 1] || '';
    if (token === '--output') args.output = argv[i + 1] || '';
    if (token === '--font') args.font = argv[i + 1] || 'serif';
  }

  return args;
}

function pickFonts(fontArg) {
  if (fontArg === 'sans-serif') return FONT_SANS;
  if (fontArg === 'serif') return FONT_SERIF;
  return fontArg;
}

async function readInput(inputPath) {
  if (inputPath) {
    return fs.readFile(inputPath, 'utf8');
  }

  let data = '';
  for await (const chunk of process.stdin) {
    data += chunk;
  }
  return data;
}

async function main() {
  const { input, output, font } = parseArgs(process.argv.slice(2));
  const markdown = await readInput(input);
  const html = convertMarkdownToWxHtml(markdown, { fonts: pickFonts(font) });

  if (output) {
    await fs.writeFile(output, html, 'utf8');
    return;
  }

  process.stdout.write(html);
}

main().catch((error) => {
  process.stderr.write(`[markdown-to-wx-html] ${error.message}\n`);
  process.exit(1);
});
