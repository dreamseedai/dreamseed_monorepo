/**
 * MathJax v3 + SRE SVG & MathSpeak 생성
 */
import {mathjax} from 'mathjax-full/js/mathjax.js';
import {TeX} from 'mathjax-full/js/input/tex.js';
import {MathML} from 'mathjax-full/js/input/mathml.js';
import {SVG} from 'mathjax-full/js/output/svg.js';
import {liteAdaptor} from 'mathjax-full/js/adaptors/liteAdaptor.js';
import {RegisterHTMLHandler} from 'mathjax-full/js/handlers/html.js';
import crypto from 'node:crypto';
import SRE from 'speech-rule-engine';

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);

const tex = new TeX({packages: ['base','ams','mhchem']});
const mml = new MathML();
const svg = new SVG({fontCache: 'local'});

const htmlTex = mathjax.document('', {InputJax: tex, OutputJax: svg});
const htmlMml = mathjax.document('', {InputJax: mml, OutputJax: svg});

SRE.setupEngine({domain: 'mathspeak', style: 'default', locale: 'en'});

export function renderToSvgHashAndSpeech({texString=null, mathml=null}) {
  let node;
  if (texString) {
    node = htmlTex.convert(texString, {display: false});
  } else if (mathml) {
    node = htmlMml.convert(mathml, {display: false});
  } else {
    throw new Error('No input');
  }
  const svgOut = adaptor.outerHTML(node);
  const hash = crypto.createHash('sha256').update(svgOut).digest('hex');
  const speech = SRE.toSpeech(texString ?? adaptor.outerHTML(node));
  return {svg: svgOut, svg_hash: hash, speech};
}
