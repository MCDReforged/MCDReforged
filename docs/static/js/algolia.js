// Algolia Docsearch implement
// https://docsearch.algolia.com/docs/api

const translations = {
  placeholder: '搜索文档',
  button: {
    buttonText: '搜索',
    buttonAriaLabel: '搜索',
  },
  modal: {
    searchBox: {
      resetButtonTitle: '清除搜索内容',
      resetButtonAriaLabel: '清除搜索内容',
      cancelButtonText: '取消',
      cancelButtonAriaLabel: '取消',
    },
    startScreen: {
      recentSearchesTitle: '最近搜索',
      noRecentSearchesText: '无最近搜索',
      saveRecentSearchButtonTitle: '保存搜索结果',
      removeRecentSearchButtonTitle: '从历史中删除',
      favoriteSearchesTitle: '收藏',
      removeFavoriteSearchButtonTitle: '从收藏夹中删除'
    },
    errorScreen: {
      titleText: '无法获取结果',
      helpText: '检查网络连接'
    },
    footer: {
      selectText: '选择',
      selectKeyAriaLabel: '回车键',
      navigateText: '导航',
      navigateUpKeyAriaLabel: '向上箭头',
      navigateDownKeyAriaLabel: '向下箭头',
      closeText: '关闭',
      closeKeyAriaLabel: 'ESC',
      searchByText: '采用',
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

// Get current language
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
    enable: '使用 Algolia Docsearch',
    disable: '使用传统搜索方式'
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
