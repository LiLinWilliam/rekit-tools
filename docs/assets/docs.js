(() => {
  const input = document.querySelector('[data-tool-search]');
  const cards = [...document.querySelectorAll('[data-tool-card]')];
  const top = document.querySelector('[data-backtop]');
  if (input) {
    input.addEventListener('input', () => {
      const query = input.value.trim().toLowerCase();
      cards.forEach(card => {
        card.hidden = query !== '' && !card.dataset.search.includes(query);
      });
    });
  }
  if (top) {
    const update = () => { top.hidden = window.scrollY < 480; };
    window.addEventListener('scroll', update, {passive: true});
    update();
    top.addEventListener('click', () => window.scrollTo({top: 0, behavior: 'smooth'}));
  }
})();
