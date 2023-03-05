// Algolia Docsearch implement
// https://docsearch.algolia.com/docs/api

const translations = {
  placeholder: '\u641c\u7d22\u6587\u6863',
  button: {
    buttonText: '\u641c\u7d22',
    buttonAriaLabel: '\u641c\u7d22',
  },
  modal: {
    searchBox: {
      resetButtonTitle: '\u6e05\u9664\u641c\u7d22\u5185\u5bb9',
      resetButtonAriaLabel: '\u6e05\u9664\u641c\u7d22\u5185\u5bb9',
      cancelButtonText: '\u53d6\u6d88',
      cancelButtonAriaLabel: '\u53d6\u6d88',
    },
    startScreen: {
      recentSearchesTitle: '\u6700\u8fd1\u641c\u7d22',
      noRecentSearchesText: '\u65e0\u6700\u8fd1\u641c\u7d22',
      saveRecentSearchButtonTitle: '\u4fdd\u5b58\u641c\u7d22\u7ed3\u679c',
      removeRecentSearchButtonTitle: '\u4ece\u5386\u53f2\u4e2d\u5220\u9664',
      favoriteSearchesTitle: '\u6536\u85cf',
      removeFavoriteSearchButtonTitle: '\u4ece\u6536\u85cf\u5939\u4e2d\u5220\u9664'
    },
    errorScreen: {
      titleText: '\u65e0\u6cd5\u83b7\u53d6\u7ed3\u679c',
      helpText: '\u68c0\u67e5\u7f51\u7edc\u8fde\u63a5'
    },
    footer: {
      selectText: '\u9009\u62e9',
      selectKeyAriaLabel: '\u56de\u8f66\u952e',
      navigateText: '\u5bfc\u822a',
      navigateUpKeyAriaLabel: '\u5411\u4e0a\u7bad\u5934',
      navigateDownKeyAriaLabel: '\u5411\u4e0b\u7bad\u5934',
      closeText: '\u5173\u95ed',
      closeKeyAriaLabel: 'ESC',
      searchByText: '\u91c7\u7528',
    }
  },
};

config = {
  appId: 'A1XIV9INYQ',
  apiKey: '43120950d3053488e5146d70643f567f', // public apiKey
  indexName: 'mcdreforgeddocs', // en_US by default
  container: '#rtd-search-form',
  debug: false
}

// Get current langeage
if (typeof READTHEDOCS_DATA !== 'undefined') {
  language = READTHEDOCS_DATA.language
} else {
  language = document.documentElement.lang
}

// Set translations
if (language.startsWith("zh")) {
  config.translations = translations;
  config.indexName = 'mcdreforgeddocs-zh_CN';
  config.placeholder = translations.placeholder;
  translations.switchgear = {
    enable: '\u4f7f\u7528 Algolia Docsearch',
    disable: '\u4f7f\u7528\u4f20\u7edf\u641c\u7d22\u65b9\u5f0f'
  }
} else {
  translations.switchgear = {
    enable: 'Use Algolia Docsearch',
    disable: 'Use Legacy Search'
  }
};

// Switchgear
// add a switchgear to allow users to still use the original search system
algolia_enabled = !document.cookie.includes('algolia=false');

if (algolia_enabled) {
  docsearch(config);
}

switchgear = document.createElement('a');
switchgear.innerText = algolia_enabled ? translations.switchgear.disable : translations.switchgear.enable;
switchgear.onclick = function () {
  if (algolia_enabled) {
    document.cookie = 'algolia=false';
  } else {
    document.cookie = 'algolia=true';
  }
  location.reload();
}
document.getElementById('rtd-search-form').append(switchgear);
