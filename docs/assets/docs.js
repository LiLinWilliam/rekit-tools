(() => {
  const input = document.querySelector('[data-tool-search]');
  const cards = [...document.querySelectorAll('[data-tool-card]')];
  const status = document.querySelector('[data-search-status]');
  const top = document.querySelector('[data-backtop]');

  const highlight = (text, query) => {
    const fragment = document.createDocumentFragment();
    if (!query) {
      fragment.append(document.createTextNode(text));
      return fragment;
    }
    const lower = text.toLowerCase();
    let cursor = 0;
    let index = lower.indexOf(query, cursor);
    while (index !== -1) {
      fragment.append(document.createTextNode(text.slice(cursor, index)));
      const mark = document.createElement('mark');
      mark.textContent = text.slice(index, index + query.length);
      fragment.append(mark);
      cursor = index + query.length;
      index = lower.indexOf(query, cursor);
    }
    fragment.append(document.createTextNode(text.slice(cursor)));
    return fragment;
  };

  const updateSearch = () => {
    const query = input ? input.value.trim().toLowerCase() : '';
    let visible = 0;
    cards.forEach(card => {
      const title = card.dataset.title || card.querySelector('h3').textContent;
      card.dataset.title = title;
      const match = query === '' || card.dataset.search.includes(query);
      card.hidden = !match;
      if (match) visible += 1;
      const heading = card.querySelector('h3');
      heading.replaceChildren(highlight(title, query));
    });
    if (status) {
      status.textContent = query === ''
        ? `Showing all ${cards.length} tool pages. Type a name or purpose to filter.`
        : visible === 0
          ? 'No matching tool pages. Try a shorter keyword.'
          : `Showing ${visible} matching tool page${visible === 1 ? '' : 's'}.`;
    }
  };

  if (input) {
    input.addEventListener('input', updateSearch);
    updateSearch();
  }
  if (top) {
    const update = () => { top.hidden = window.scrollY < 480; };
    window.addEventListener('scroll', update, {passive: true});
    update();
    top.addEventListener('click', () => window.scrollTo({top: 0, behavior: 'smooth'}));
  }
})();
