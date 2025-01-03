window.addEventListener('load', () => {
    let flyout = document.querySelector('readthedocs-flyout').shadowRoot;
    let main = flyout.querySelector("main");
    main.addEventListener('click', (e) => {
        e.stopPropagation();
    });
})