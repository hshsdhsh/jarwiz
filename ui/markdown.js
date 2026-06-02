/* ═══════════════════════════════════════════
   JarWiz — Markdown Renderer (simple)
═══════════════════════════════════════════ */

/**
 * Minimal markdown parser for AI responses
 * Handles: code blocks, inline code, bold, headers, lists, links
 */
function renderMarkdown(text) {
  // Escape HTML first (except within code blocks)
  let segments = [];
  let lastIdx = 0;

  // Extract code blocks first to prevent processing their contents
  const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
  let match;
  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      segments.push({ type: 'text', content: text.slice(lastIdx, match.index) });
    }
    segments.push({ type: 'code', lang: match[1] || 'text', content: match[2] });
    lastIdx = match.index + match[0].length;
  }
  if (lastIdx < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIdx) });
  }

  return segments.map(seg => {
    if (seg.type === 'code') {
      const escaped = escapeHtml(seg.content.trimEnd());
      return `<pre><code class="lang-${seg.lang}">${escaped}</code></pre>`;
    }
    return processText(seg.content);
  }).join('');
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function processText(text) {
  // Strip the hidden <cmd>...</cmd> blocks
  text = text.replace(/<cmd>[\s\S]*?<\/cmd>/g, '');

  // Headers
  text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Bold + italic
  text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Inline code
  text = text.replace(/`([^`]+)`/g, (_, c) => `<code>${escapeHtml(c)}</code>`);

  // Links
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Unordered lists
  text = text.replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>');
  text = text.replace(/(<li>[\s\S]*?<\/li>)(?=\n<li>|$)/g, (match) => `<ul>${match}</ul>`);
  // Simplify nested ul cleanup
  text = text.replace(/<\/ul>\n<ul>/g, '');

  // Ordered lists
  text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // Horizontal rule
  text = text.replace(/^---$/gm, '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:12px 0"/>');

  // Paragraphs (double newline)
  text = text.replace(/\n\n+/g, '</p><p>');
  text = '<p>' + text + '</p>';

  // Single line breaks inside paragraphs
  text = text.replace(/\n/g, '<br/>');

  // Clean up empty paragraphs
  text = text.replace(/<p><\/p>/g, '');
  text = text.replace(/<p>(<h[1-6]>)/g, '$1');
  text = text.replace(/(<\/h[1-6]>)<\/p>/g, '$1');
  text = text.replace(/<p>(<ul>)/g, '$1');
  text = text.replace(/(<\/ul>)<\/p>/g, '$1');
  text = text.replace(/<p>(<hr)/g, '$1');
  text = text.replace(/<p>(<pre>)/g, '$1');

  return text;
}
