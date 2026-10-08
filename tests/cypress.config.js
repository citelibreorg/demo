const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost/citelibre-rendezvous/jsp/admin/AdminMessage.jsp',
    experimentalStudio:true,
    setupNodeEvents(on, config) {
      // implement node event listeners here

    },

  },
  reporter: 'cypress-multi-reporters',
  reporterOptions: {
    configFile: 'reporter-config.json',
  },
});
