function waitForElement(selector, callback) {
    if (document.querySelector(selector)) {
        callback();
    } else {
        setTimeout(function() {
            waitForElement(selector, callback);
        }, 100);
    }
}

window.addEventListener('load', () => {
    waitForElement('readthedocs-flyout', () => {
        let flyout = document.querySelector('readthedocs-flyout').shadowRoot;
        let main = flyout.querySelector("main");
        main.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    })
})
