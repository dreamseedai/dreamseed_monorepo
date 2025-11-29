"use client";

import { useEffect, useRef, useState } from 'react';
import { Editor } from '@tinymce/tinymce-react';

// TinyMCE 4 types (actual version in use)
// Note: @types/tinymce is for v5/6, so we use a compatible interface for v4
interface TinyMCEEditor {
  id: string;
  getContainer(): HTMLElement;
  getBody(): HTMLElement;
  getDoc(): Document;
  getContent(): string;
  setContent(content: string): void;
  insertContent(content: string): void;
  selection: {
    getNode(): HTMLElement;
    setContent(content: string): void;
  };
  windowManager: {
    open(config: any): any;
    openUrl(config: any): any;
  };
  ui: {
    registry: {
      addButton(name: string, config: any): void;
      addContextToolbar(name: string, config: any): void;
    };
  };
  on(event: string, callback: Function): void;
  addCommand(name: string, callback: Function): void;
  execCommand(command: string): void;
}

interface RichTextEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  height?: number; // fixed height (ignored when autoHeight=true)
  autoHeight?: boolean; // enable TinyMCE autoresize
  minHeight?: number; // min height when autoHeight
  maxHeight?: number; // optional max height when autoHeight
  disabled?: boolean;
}

export function RichTextEditor({ value, onChange, placeholder, height = 400, autoHeight = false, minHeight, maxHeight, disabled }: RichTextEditorProps) {
  const editorRef = useRef<TinyMCEEditor | null>(null);
  const [licenseKey, setLicenseKey] = useState<string>('gpl');
  const editorId = useRef(`tinymce-editor-${Math.random().toString(36).substr(2, 9)}`);

  // Initialize TinyMCE license key from localStorage or env, fallback to GPL
  useEffect(() => {
    try {
      const stored = typeof window !== 'undefined' ? window.localStorage.getItem('tinymce_license_key') : null;
      const envKey = process.env.NEXT_PUBLIC_TINYMCE_LICENSE_KEY;
      const key = (stored && stored.trim()) || (envKey && envKey.trim()) || 'gpl';
      setLicenseKey(key);
    } catch {
      setLicenseKey('gpl');
    }
  }, []);

  useEffect(() => {
    // 클라이언트 사이드에서만 실행
    if (typeof window === 'undefined') return;

    // MathLive 및 KaTeX 동적 로드
    const loadMathDeps = async () => {
      if (!(window as any).katex) {
        const katexCSS = document.createElement('link');
        katexCSS.rel = 'stylesheet';
        katexCSS.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css';
        document.head.appendChild(katexCSS);

        const katexJS = document.createElement('script');
        katexJS.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js';
        await new Promise((resolve) => {
          katexJS.onload = resolve;
          katexJS.onerror = resolve; // Continue even if fails
          document.head.appendChild(katexJS);
        });
      }

      if (!(window as any).MathfieldElement) {
        const mathLiveJS = document.createElement('script');
        // Use a specific stable version
        mathLiveJS.src = 'https://cdn.jsdelivr.net/npm/mathlive@0.95.5/dist/mathlive.min.js';
        await new Promise((resolve) => {
          mathLiveJS.onload = resolve;
          mathLiveJS.onerror = () => {
            console.warn('MathLive failed to load, math input may not work');
            resolve(null);
          };
          document.head.appendChild(mathLiveJS);
        });
      }
    };

    loadMathDeps();
  }, []);

  // MathLive 플러그인 설정
  const setupMathPlugin = (editor: TinyMCEEditor) => {
    const openMathDialog = () => {
      const node = editor.selection.getNode() as HTMLElement;
      const isEdit = node?.classList?.contains('ds-math');
      const existingLatex = isEdit ? decodeURIComponent(node.dataset?.latex || '') : '';

      editor.windowManager.open({
        title: isEdit ? '수식 편집' : '수식 삽입',
        body: {
          type: 'panel',
          items: [
            {
              type: 'htmlpanel',
              html: `<div style="padding: 10px;">
                <math-field id="mf-${Date.now()}" 
                  style="width:100%; min-height:60px; font-size:1.2rem; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
                  virtual-keyboard-mode="manual">${existingLatex || ''}</math-field>
                <div style="margin-top: 8px; font-size: 12px; color: #666;">
                  수식을 입력하세요. 예: x^2 + 2x + 1 = 0
                </div>
              </div>`
            }
          ]
        },
        buttons: [
          { type: 'cancel', text: '취소' },
          { type: 'submit', text: isEdit ? '수정' : '삽입', primary: true }
        ],
        onSubmit: (api: any) => {
          const mf = document.querySelector('math-field') as any;
          const latex = mf?.getValue ? mf.getValue() : '';
          
          if (latex && latex.trim()) {
            try {
              const katex = (window as any).katex;
              const html = katex.renderToString(latex, {
                throwOnError: false,
                displayMode: false,
                trust: true,
                output: 'html',
              });
              const encoded = encodeURIComponent(latex);
              const mathHtml = `<span class="ds-math" data-latex="${encoded}" contenteditable="false">${html}</span>&nbsp;`;
              
              if (isEdit) {
                editor.selection.setContent(mathHtml);
              } else {
                editor.insertContent(mathHtml);
              }
            } catch (e) {
              console.error('수식 렌더링 실패:', e);
              alert('수식 렌더링에 실패했습니다.');
            }
          }
          api.close();
        }
      });
    };

    // Math 버튼
    editor.ui.registry.addButton('dsMath', {
      tooltip: '수식 삽입',
      icon: 'formula',
      onAction: () => openMathDialog(),
    });

    // 명령어 등록: 더블클릭/컨텍스트에서 재사용
    editor.addCommand('mceToggleDsMath', () => openMathDialog());

    // Math 컨텍스트 툴바
    editor.ui.registry.addContextToolbar('dsMathCtx', {
      predicate: (node: any) => (node as HTMLElement)?.classList?.contains('ds-math'),
      items: 'dsMathEdit dsMathDelete',
      position: 'node'
    });

    editor.ui.registry.addButton('dsMathEdit', {
      text: '편집',
      onAction: () => {
        const node = editor.selection.getNode() as HTMLElement;
        if (node?.classList?.contains('ds-math')) {
          editor.execCommand('mceToggleDsMath');
        }
      }
    });

    editor.ui.registry.addButton('dsMathDelete', {
      text: '삭제',
      onAction: () => {
        const node = editor.selection.getNode() as HTMLElement;
        if (node?.classList?.contains('ds-math')) {
          node.remove();
        }
      }
    });

    // 더블클릭으로 수식 편집
    editor.on('DblClick', (e: any) => {
      const el = e.target as HTMLElement;
      if (el?.classList?.contains('ds-math')) {
        editor.execCommand('mceToggleDsMath');
      }
    });
  };

  return (
    <div className="space-y-1">
      <Editor
        key={`tinymce-${licenseKey}-${autoHeight ? 'auto' : 'fixed'}`}
        tinymceScriptSrc="/tinymce/tinymce.min.js"
        value={value}
        onInit={(evt: any, editor: any) => {
          editorRef.current = editor;
          
          // Apply license key after init
          if (licenseKey && licenseKey !== 'gpl' && (window as any).tinymce) {
            try {
              (window as any).tinymce.EditorManager.EditorManager && 
              ((window as any).tinymce.EditorManager.EditorManager.licenseKey = licenseKey);
            } catch {}
          }
          
          // TinyMCE 4 + WIRIS 확인
          setTimeout(() => {
            console.log('TinyMCE version:', (window as any).tinymce?.majorVersion);
            console.log('WIRIS loaded:', !!(window as any).WirisPlugin);
          }, 500);
        }}
        onEditorChange={(newValue: any) => onChange(newValue)}
        disabled={disabled}
        init={{
          // When autoHeight is enabled, omit fixed height and rely on autoresize
          ...(autoHeight ? {} : { height }),
          menubar: false,
          content_css: false,
          skin_url: '/tinymce/skins/lightgray',
          // Preserve as much markup as possible to allow MathML/TeX containers through
          verify_html: false,
          valid_elements: '*[*]',
          // Preserve MathML/TeX containers in content (avoid TinyMCE stripping)
          custom_elements: 'math,mrow,mi,mo,mn,msqrt,mfrac,msup,msub,msubsup,munder,mover,munderover,mtable,mtr,mtd,mstyle,mspace,menclose,mtext,ms,mglyph,semantics,annotation,annotation-xml,mml|math,mml|mrow,mml|mi,mml|mo,mml|mn,mml|msqrt,mml|mfrac,mml|msup,mml|msub,mml|msubsup,mml|munder,mml|mover,mml|munderover,mml|mtable,mml|mtr,mml|mtd,mml|mstyle,mml|mspace,mml|menclose,mml|mtext,mml|ms,mml|mglyph,mml|semantics,mml|annotation,mml|annotation-xml',
          extended_valid_elements: 'math[*],mrow[*],mi[*],mo[*],mn[*],msqrt[*],mfrac[*],msup[*],msub[*],msubsup[*],munder[*],mover[*],munderover[*],mtable[*],mtr[*],mtd[*],mstyle[*],mspace[*],menclose[*],mtext[*],ms[*],mglyph[*],semantics[*],annotation[*],annotation-xml[*],mml|math[*],mml|mrow[*],mml|mi[*],mml|mo[*],mml|mn[*],mml|msqrt[*],mml|mfrac[*],mml|msup[*],mml|msub[*],mml|msubsup[*],mml|munder[*],mml|mover[*],mml|munderover[*],mml|mtable[*],mml|mtr[*],mml|mtd[*],mml|mstyle[*],mml|mspace[*],mml|menclose[*],mml|mtext[*],mml|ms[*],mml|mglyph[*],mml|semantics[*],mml|annotation[*],mml|annotation-xml[*]',
          valid_children: '+body[math],+div[math],+p[math],+span[math]',
          entity_encoding: 'raw',
          plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'media', 'table', 'contextmenu', 'paste', 'textcolor',
            ...(autoHeight ? [] : [])
          ],
          external_plugins: {
            'tiny_mce_wiris': 'https://cdn.jsdelivr.net/npm/@wiris/mathtype-tinymce4/plugin.min.js'
          },
          toolbar1: 'undo redo | code fullscreen | bold italic underline | forecolor backcolor | link image table',
          toolbar2: 'formatselect fontselect fontsizeselect | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | tiny_mce_wiris_formulaEditor tiny_mce_wiris_formulaEditorChemistry | dsMath | removeformat',
          content_style: `
            body { 
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important; 
              font-size: 14px !important; 
              line-height: 1.6 !important;
              white-space: normal !important;
              word-wrap: break-word !important;
            }
            .mce-content-body { 
              color: #0f172a !important; 
              background: #ffffff !important; 
              white-space: normal !important; 
            }
            :root.dark .mce-content-body { color: #e5e7eb !important; background: #0b1220 !important; }
            
            /* 모든 요소 기본 설정 */
            * { box-sizing: border-box; }
            p, div, span { white-space: normal !important; line-height: 1.6 !important; }
            
            /* Native MathML rendering - 최강 우선순위 */
            math {
              display: inline-block !important;
              vertical-align: middle !important;
              line-height: 1 !important;
              white-space: nowrap !important;
              font-family: "STIX Two Math", "Cambria Math", "Latin Modern Math", serif !important;
              margin: 0 !important;
              padding: 0 !important;
              overflow: visible !important;
              max-width: none !important;
              width: auto !important;
            }
            math[display="block"] {
              display: block !important;
              text-align: center !important;
              margin: 0.75em 0 !important;
              white-space: normal !important;
            }
            
            /* MathML fraction - 강제 인라인 */
            mfrac {
              display: inline-table !important;
              vertical-align: -0.6em !important;
              text-align: center !important;
              padding: 0 0.2em !important;
              white-space: normal !important;
              min-width: fit-content !important;
              border-collapse: collapse !important;
            }
            mfrac > * {
              display: table-row !important;
              font-size: 0.9em !important;
              line-height: 1.2 !important;
              white-space: normal !important;
              min-width: fit-content !important;
              text-align: center !important;
            }
            mfrac > :first-child {
              border-bottom: 1px solid currentColor !important;
              padding-bottom: 0.15em !important;
              margin: 0 !important;
            }
            mfrac > :last-child {
              padding-top: 0.15em !important;
              margin: 0 !important;
            }
            
            /* mstyle은 투명 컨테이너 */
            mstyle {
              display: inline !important;
              white-space: normal !important;
              font-size: inherit !important;
              margin: 0 !important;
              padding: 0 !important;
            }
            mstyle[displaystyle="false"] {
              display: inline !important;
            }
            mstyle[displaystyle="true"] {
              display: block !important;
            }
            
            /* Other MathML elements - 강제 인라인 */
            msup, msub, msubsup, msqrt, mroot {
              display: inline-block !important;
              vertical-align: baseline !important;
              white-space: nowrap !important;
              line-height: 1 !important;
              min-width: fit-content !important;
            }
            msup > :last-child { font-size: 0.7em !important; vertical-align: super !important; }
            msub > :last-child { font-size: 0.7em !important; vertical-align: sub !important; }
            msqrt { 
              padding: 0.1em 0.3em 0.1em 0.2em !important;
              border-top: 0.08em solid currentColor !important;
              position: relative !important;
              min-width: fit-content !important;
            }
            msqrt::before {
              content: '√' !important;
              position: absolute !important;
              left: -0.1em !important;
              font-size: 1.2em !important;
            }
            mroot { vertical-align: middle !important; min-width: fit-content !important; }
            mi { font-style: italic !important; display: inline !important; }
            mn { font-style: normal !important; display: inline !important; }
            mo { 
              font-style: normal !important; 
              padding: 0 0.2em !important;
              display: inline !important;
              white-space: nowrap !important;
            }
            mtext { font-style: normal !important; display: inline !important; }
            mrow { 
              display: inline !important; 
              white-space: nowrap !important;
              min-width: fit-content !important;
            }
            
            /* Brackets and fences - 절대 줄바꿈 금지 */
            mo[stretchy="true"], mo.fence, mo[fence="true"] {
              font-size: 1.5em !important;
              vertical-align: middle !important;
              display: inline !important;
              white-space: nowrap !important;
            }
            
            /* 괄호로 감싸진 콘텐츠 - 강제 한 줄 */
            mrow:has(> mo[fence="true"]),
            mrow:has(> mo:first-child),
            mfenced {
              display: inline-flex !important;
              flex-wrap: nowrap !important;
              white-space: nowrap !important;
              align-items: center !important;
            }
            
            .ds-math {
              display: inline-block !important;
              padding: 2px 6px !important;
              margin: 0 2px !important;
              background: rgba(59, 130, 246, 0.1) !important;
              border: 1px solid rgba(59, 130, 246, 0.3) !important;
              border-radius: 4px !important;
              cursor: pointer !important;
              user-select: none !important;
              white-space: nowrap !important;
            }
            .katex { white-space:nowrap !important; display:inline !important; }
            .katex-display { display:block !important; white-space:normal !important; margin:.5em 0 !important; }
            .ds-math:hover {
              background: rgba(59, 130, 246, 0.2) !important;
              border-color: rgba(59, 130, 246, 0.5) !important;
            }
            img.ds-chem {
              max-width: 100% !important;
              height: auto !important;
              display: inline-block !important;
              vertical-align: middle !important;
              border: 1px solid #e5e7eb !important;
              border-radius: 4px !important;
              padding: 4px !important;
              margin: 4px !important;
            }
          `,
          placeholder: placeholder || '내용을 입력하세요...',
          skin: 'lightgray',
          theme: 'modern',
            // TinyMCE 4 setup callback
            setup: (editor: any) => {
              // 커스텀 Math 버튼 (KaTeX 기반) - 간단한 구현
              editor.addButton('dsMath', {
              text: 'Math',
              icon: false,
              onclick: () => {
                const latex = prompt('수식을 입력하세요 (LaTeX):', 'x^2 + 1');
                if (latex && (window as any).katex) {
                  try {
                    const html = (window as any).katex.renderToString(latex, {
                      throwOnError: false,
                      displayMode: false,
                    });
                    editor.insertContent(`<span class="ds-math" data-latex="${encodeURIComponent(latex)}" contenteditable="false">${html}</span>&nbsp;`);
                  } catch (e) {
                    alert('수식 렌더링 실패');
                  }
                }
              }
            });
            
            // 커스텀 Chem 버튼 - 간단한 구현
            editor.addButton('dsChem', {
              text: 'Chem',
              icon: false,
              onclick: () => {
                alert('화학 구조식 에디터는 WIRIS ChemType 버튼을 사용하세요');
              }
            });
          },
          // Autoresize options - TinyMCE 4 style
          ...(autoHeight ? {
            autoresize_min_height: minHeight || 100,
            autoresize_max_height: maxHeight || 500,
          } : {}),
          contextmenu: 'link image table',
          paste_data_images: true,
          automatic_uploads: false,
          file_picker_types: 'image',
          images_upload_handler: async (blobInfo: any) => {
            // Base64 인코딩으로 이미지 처리
            return new Promise<string>((resolve) => {
              const reader = new FileReader();
              reader.onload = () => {
                resolve(reader.result as string);
              };
              reader.readAsDataURL(blobInfo.blob());
            });
          },
        }}
      />
    </div>
  );
}

