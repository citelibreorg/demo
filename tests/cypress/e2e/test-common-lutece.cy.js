describe('Cite Libre :: Rendez Vous', () => {
  it('Login and navigate through common features', () => {
    Cypress.on('uncaught:exception', (err, runnable) => {
      // bypass uncaught errors thrown by Lutece framework scripts
      return false
    })
    cy.visit(Cypress.config("baseUrl")) // get to backoffice main page
        .get('button[title="OK"]').click() // accept user warning and redirect to keycloak authent
        .get('#username').type("admin@paris.fr")
        .get('#password').type("coucou")
        .get('#kc-login').click(); // login;
    cy.get('#menu-mobile i.ti').click();
    cy.get('#main-menu a[href="#SYSTEM"]').click();
    cy.get('#right-list a[feature-url="jsp/admin/system/ManagePlugins.jsp"] h3.mb-1 span').click();
    cy.get('#menu-mobile i.ti').click();
    cy.get('#main-menu a.feature-link.text-center div.menu-label').click();
    cy.get('#menu-mobile').click();
    cy.get('#main-menu a[href="#MANAGERS"] div.menu-label').click();
    cy.get('#right-list a[feature-url="jsp/admin/user/ManageUsers.jsp"] h3.mb-1 span').click();
    cy.get('tr:nth-of-type(1) #portlet-type span.d-none').click();
    cy.get('tr:nth-of-type(1) #portlet-type span.d-none').click();
    cy.get('tr:nth-of-type(2) #portlet-type span.d-none').click();
    cy.get('#portlet-type a[href="jsp/admin/user/ModifyUserRights.jsp?id_user=5"]').click();
    cy.get('#Gestion\\ des\\ en-têtes\\ de\\ sécurité').check({force: true});
    cy.get('#Gestion\\ des\\ mappings\\ NotifyGru\\ et\\ Manager').check({force: true});
    cy.get('#module\\.appointment\\.management\\.adminFeature\\.AppointmentSearch\\.name').check({force: true});
    cy.get('#lutece-page-wrapper div.pt-3 div:nth-child(2) button.btn').click({force: true});
  });

  it('Login and navigate through workflow configuration', function() {
    Cypress.on('uncaught:exception', (err, runnable) => {
      // bypass uncaught errors thrown by Lutece framework scripts
      return false
    })
    cy.visit(Cypress.config("baseUrl"))
    cy.get('i.ti').click();
    cy.get('[name="username"]').click();
    cy.get('[name="username"]').type('admin@paris.fr');
    cy.get('[name="password"]').type('coucou');
    cy.get('[name="login"]').click();
    cy.get('#menu-mobile i.ti').click();
    cy.get('#main-menu a[href="#MANAGERS"] div.menu-label').click();
    cy.get('#right-list a[feature-url="jsp/admin/mailinglist/ManageMailingLists.jsp"] h3.mb-1 span').click();
    cy.get('#menu-mobile').click();
    cy.get('#main-menu a[href="#SYSTEM"] div.menu-label').click();
    cy.get('#right-list a[feature-url="jsp/admin/plugins/kibana/KibanaDashboard.jsp"] h3.mb-1 span').click();
    cy.get('#menu-mobile').click();
    cy.get('#main-menu a.active div.menu-label').click();
    cy.get('#right-list a[feature-url="jsp/admin/plugins/workflow/ManageWorkflow.jsp"] h3.mb-1 span').click();
    cy.get('#lutece-page-wrapper div.lutece-column').click();
    cy.get('#lutece-page-wrapper a[href="jsp/admin/plugins/workflow/ModifyWorkflow.jsp?id_workflow=1"]').click();
    cy.get('#lutece-page-wrapper [name="save"] span.d-xxl-inline-flex').click();
  });
});
