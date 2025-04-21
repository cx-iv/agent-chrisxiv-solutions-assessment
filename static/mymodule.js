console.log("IM HERE!!!!! THE FUNCTION IS HERE!!!!")


const copyBtn = document.querySelector('button[data-writer-id="6vik4jn5i3a0ldrc"]');
if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      // your click‑handler logic here:
      console.log('Copy button clicked! SOMETHING SHOULD BE COPIED');
      const text = document.querySelector('section[data-writer-id="2n758fe37xqhb9qw"] .plainText').innerText;
      navigator.clipboard.writeText(text);
      // e.g. copy some text to clipboard...
    });
}