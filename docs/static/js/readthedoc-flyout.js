// function waitForElement(selector, callback) {
//     if (document.querySelector(selector)) {
//         callback();
//     } else {
//         setTimeout(function() {
//             waitForElement(selector, callback);
//         }, 100);
//     }
// }

window.addEventListener('readthedocs-addons-data-ready', () => {
    // waitForElement('readthedocs-flyout', () => {
    let flyout = document.querySelector('readthedocs-flyout').shadowRoot;
    let target = flyout.querySelector("header");
    target.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    // })
})
