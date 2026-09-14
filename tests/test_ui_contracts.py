from pathlib import Path

from jinja2 import Environment, FileSystemLoader


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_all_jinja_templates_parse():
    environment = Environment(loader=FileSystemLoader(TEMPLATES))

    for template_path in TEMPLATES.rglob("*.j2"):
        source = template_path.read_text(encoding="utf-8")
        environment.parse(source)


def test_base_owns_document_structure():
    base = read("templates/base.j2")
    footer = read("templates/shared/footer.j2")

    assert base.count("<head>") == 1
    assert base.count("</head>") == 1
    assert base.count("<body") == 1
    assert base.count("</body>") == 1
    assert base.count("</html>") == 1
    assert "</body>" not in footer
    assert "</html>" not in footer


def test_visual_assets_load_after_legacy_styles():
    head = read("templates/components/head.j2")

    assert head.index("css/ux.css") > head.index("css/modal.css")
    assert "js/ui.js" in head
    assert "IBM+Plex+Mono" in head


def test_shell_accessibility_contracts_exist():
    base = read("templates/base.j2")
    navigation = read("templates/components/dropdown/dropdown-cde.j2")
    runtime = read("templates/components/app-runtime.j2")

    assert 'href="#main-content"' in base
    assert 'id="main-content"' in base
    assert 'aria-label="Navegação principal"' in navigation
    assert 'aria-controls="navigation-menu"' in navigation
    assert 'id="navigation-menu"' in navigation
    assert 'aria-live="polite"' in runtime


def test_navigation_script_only_changes_navigation_state():
    script = read("static/js/ui.js")

    assert "navigation-bar" in script
    assert "navigation-toggle" in script
    assert "fetch(" not in script
    assert "XMLHttpRequest" not in script
    assert ".submit(" not in script


def test_home_keeps_every_existing_action():
    action_component = read("templates/components/home/action-card.j2")
    expected_actions = {
        "templates/pages/index/cde-index.j2": {
            "home_prod",
            "cde_profile",
            "home_logi",
            "users",
            "cde_cfg",
            "about",
        },
        "templates/pages/index/tl-index.j2": {
            "cargas",
            "faturado",
            "mov_request",
            "estoque",
            "mov",
            "historico",
        },
        "templates/pages/index/hp-index.j2": {
            "producao",
            "etiqueta",
            "envase",
            "rotulo",
            "produtos",
        },
    }

    assert 'class="item{% if featured %} featured{% endif %}"' in action_component
    assert "window.location.href='{{ url_for(endpoint) }}'" in action_component

    for template, endpoints in expected_actions.items():
        source = read(template)
        assert source.count("home_action(") == len(endpoints)
        for endpoint in endpoints:
            assert f"home_action('{endpoint}'" in source


def test_home_module_identity_uses_shared_component():
    component = read("templates/components/home/module-card.j2")
    templates = (
        "templates/pages/index/cde-index.j2",
        "templates/pages/index/tl-index.j2",
        "templates/pages/index/hp-index.j2",
    )

    assert 'class="home-module-card"' in component
    assert 'class="home-module-icon"' in component
    assert "ui_icon(icon" in component
    assert "{% if tagline %}" in component
    for template in templates:
        assert read(template).count("home_module_card(") == 1


def test_settings_hub_keeps_every_destination_in_shared_cards():
    settings = read("templates/pages/cde/cfg-index.j2")
    component = read("templates/components/settings/setting-card.j2")
    endpoints = {
        "api",
        "cde_notifications",
        "cde_query_list",
        "users",
        "permissions",
        "admin_migrations",
    }

    assert 'class="settings-page"' in settings
    assert 'class="settings-card"' in component
    assert 'href="{{ url_for(endpoint) }}"' in component
    assert settings.count("setting_card(") == len(endpoints)
    for endpoint in endpoints:
        assert f"setting_card('{endpoint}'" in settings


def test_profile_keeps_account_actions_in_responsive_workspace():
    profile = read("templates/pages/account.j2")
    action_row = read("templates/components/action-row.j2")
    styles = read("static/css/ux.css")

    assert 'class="profile-page"' in profile
    assert 'class="profile-overview"' in profile
    assert 'class="profile-layout"' in profile
    assert "session.get('user_initials', '?')" in profile
    assert "session.get('user_name')" in profile
    assert "session.get('user_grant', 99)" in profile
    assert "action_row('change_password'" in profile
    assert "action_row('logout'" in profile
    assert 'href="{{ url_for(endpoint) }}"' in action_row
    assert ".profile-overview" in styles
    assert "@media (max-width: 680px)" in styles


def test_user_admin_pages_keep_crud_permissions_and_password_reset_contracts():
    users = read("templates/pages/users/users.j2")
    user_edit = read("templates/pages/users/users-edit.j2")
    avatar = read("templates/components/users/user-avatar.j2")
    switch = read("templates/components/switch.j2")
    styles = read("static/css/ux.css")
    backend = read("cde.py")

    for field in ("login_user", "nome_user", "sobrenome_user", "privilege_user"):
        assert f'name="{field}"' in users
    assert "url_for('cadastrar_usuario')" in users
    assert 'class="users-page"' in users
    assert 'id="createUserModal"' in users
    assert "openCreateUserModal()" in users
    assert "Modal.open('createUserModal')" in users
    assert 'class="modal users-create-modal"' in users
    assert 'class="users-open-create"' in users
    assert "permission_count" in users
    assert "users-status-deactivated" in users
    assert "Desativado" in users
    assert "function filterUsers()" in users
    assert "redirectToEdit" in users
    assert "user_avatar(item['user_name'])" in users
    assert 'class="user-avatar' in avatar

    assert 'class="user-edit-page"' in user_edit
    assert "confirmAdicionar" in user_edit
    assert "confirmRemover" in user_edit
    assert "session.get('user_grant', 99) <= 2" in user_edit
    assert "fetch('/api/users/set-password'" in user_edit
    assert "newPassword.length < 6" in user_edit
    assert "newPassword !== confirmPassword" in user_edit
    assert "response.ok" in user_edit
    assert "switch_control(" in user_edit
    assert "deactivateUser" in user_edit
    assert "item['privilege_user'] > 2" in user_edit
    assert "/users/deactivate/" in user_edit
    assert 'class="switch-control"' in switch
    assert "UserUtils.remove_all_permissions(id_user)" in backend
    assert '@app.route("/users/deactivate/<int:id_user>/"' in backend
    assert "if not cde.is_admin():" in backend
    assert 'user_data[0]["privilege_user"] <= 2' in backend
    assert ".users-overview" in styles
    assert ".user-edit-layout" in styles
    assert ".users-layout-directory" in styles
    assert ".users-create-modal" in styles
    assert ".users-status-deactivated" in styles
    assert ".switch-control input:checked + span" in styles
    assert ".user-deactivate-trigger" in styles
    assert "COUNT(up.id_perm)" in backend
    assert '"permission_count": row[5]' in backend
    assert 'if not UserUtils.set_password(id_user, password):' in backend


def test_contracts_page_uses_modern_directory_and_modal_forms():
    contracts = read("templates/pages/cde-permissions.j2")
    styles = read("static/css/ux.css")

    assert 'class="contracts-page"' in contracts
    assert 'id="createContractModal"' in contracts
    assert 'id="editContractModal"' in contracts
    assert "openContractModal('createContractModal')" in contracts
    assert "openContractModal('editContractModal')" in contracts
    assert "filterContracts()" in contracts
    assert "url_for('permissions')" in contracts
    assert "url_for('permissions_id'" in contracts
    assert 'name="id_perm_add"' in contracts
    assert 'name="desc_perm_add"' in contracts
    assert 'name="id_perm"' in contracts
    assert 'name="desc_perm"' in contracts
    assert "name='paid_feature_add'" in contracts
    assert "name='paid_feature'" in contracts
    assert "contracts-type-paid" in contracts
    assert "switch_control(" in contracts
    assert "session['user_grant'] == 1" in contracts
    assert ".contracts-overview" in styles
    assert ".contracts-modal" in styles
    assert ".contracts-table" in styles
    assert ".contracts-paid-toggle" in styles


def test_navigation_indexes_paid_modules_as_disabled_when_unlicensed():
    navigation = read("templates/components/dropdown/dropdown-cde.j2")
    styles = read("static/css/ux.css")
    backend = read("cde.py")
    license_manager = read("app/services/licenseManager.py")
    estoque_section = navigation.split("MOV004 | ESTOQUE", 1)[1].split("MOV006 | CARGAS", 1)[0]

    assert "paid_feature_locked(page_id)" in navigation
    assert "dropdown-disabled" in navigation
    assert "MOV008 | MAPA ESTOQUE" in navigation
    assert "PRC010 | PROCESSAMENTO" in navigation
    assert "ENV006 | ENVASE" in navigation
    assert "NÃO CONTRATADO" not in navigation
    assert "MOV008 | MAPA ESTOQUE" not in estoque_section
    assert navigation.index("MOV007 | REQUISIÇÕES") < navigation.index(
        "MOV008 | MAPA ESTOQUE"
    ) < navigation.index("PRODUÇÃO")
    assert "dropdown-coming-soon" in navigation
    assert "dropdown-status-badge" in navigation
    assert "EM BREVE" in navigation
    assert "is_paid_feature_locked" in backend
    assert "deny_license_access" in backend
    assert 'DEFAULT_PAID_MODULES = {"MOV008", "PRC010", "ENV006"}' in license_manager
    assert ".dropdown-disabled" in styles
    assert ".dropdown-status-badge" in styles


def test_shared_icons_do_not_depend_on_inversion_filters():
    icon = read("templates/components/icon.j2")
    styles = read("static/css/ux.css")
    movement = read("templates/pages/mov/mov.j2")
    labels = read("templates/pages/etiqueta.j2")

    assert 'class="ui-icon' in icon
    assert "--ui-icon-source" in icon
    assert "background-color: currentColor" in styles
    assert "mask: var(--ui-icon-source)" in styles
    assert movement.count("scanner-submit") == 1
    assert labels.count("scanner-submit") == 1
    assert 'type="image"' not in movement
    assert 'type="image"' not in labels


def test_label_calculator_has_its_own_responsive_layout():
    calculator = read("templates/pages/rotulo.j2")
    styles = read("static/css/ux.css")
    field_ids = {
        "diametro_inicial",
        "diametro_minimo",
        "espessura_fita",
        "espessura_papelao",
        "compr_rotulo",
    }

    assert 'class="label-calculator-page"' in calculator
    assert 'class="label-calculator-shell"' in calculator
    assert 'class="form-login"' not in calculator
    assert 'class="side-banner"' not in calculator
    assert 'id="dynamicImage"' in calculator
    for field_id in field_ids:
        assert f'id="{field_id}"' in calculator
    assert ".label-calculator-layout" in styles
    assert "@media (max-width: 900px)" in styles


def test_label_generator_keeps_generation_and_history_contracts():
    generator = read("templates/pages/etiqueta.j2")
    styles = read("static/css/ux.css")
    field_ids = {
        "input_code",
        "desc_item",
        "cod_item",
        "lote_item",
        "imgDownload",
        "label-success",
    }

    assert 'class="label-generator-page"' in generator
    assert 'class="label-generator-shell"' in generator
    assert 'id="formBuscarItens"' in generator
    assert 'id="form-field"' in generator
    assert generator.count('id="qrCodeImage') == 9
    for field_id in field_ids:
        assert f'id="{field_id}"' in generator
    assert ".label-generator-layout" in styles
    assert ".label-generator-page .qr-grid" in styles
    assert "@media (max-width: 760px)" in styles


def test_stock_map_keeps_inventory_contract_and_working_controls():
    stock_map = read("templates/pages/stock-map.j2")
    styles = read("static/css/ux.css")

    assert 'class="stock-map-page"' in stock_map
    assert 'class="stock-map-shell"' in stock_map
    assert 'id="map-container"' in stock_map
    assert 'id="map"' in stock_map
    assert "fetch('/get/stock_items/', { cache: 'no-store' })" in stock_map
    assert "parseStockAddress(item.address)" in stock_map
    assert "function renderStockMap(data)" in stock_map
    assert "function loadStockMap()" in stock_map
    assert "const mapLayout" not in stock_map
    assert "aisles.forEach(generateAisle)" in stock_map
    assert "--map-columns" in stock_map
    assert "zoomMap(0.15)" in stock_map
    assert "zoomMap(-0.15)" in stock_map
    assert "fitMap()" in stock_map
    assert "toggleMapFilters()" in stock_map
    assert 'id="stockAddressModal"' in stock_map
    assert "const stockItemsByAddress = new Map()" in stock_map
    assert "function openAddressModal(address)" in stock_map
    assert "Modal.open('stockAddressModal')" in stock_map
    assert "pressedAddress = e.target.closest('.map-cell')?.dataset.address || null" in stock_map
    assert "if (pressedAddress && !hasDragged) openAddressModal(pressedAddress)" in stock_map
    assert "function toggleMapFullscreen()" in stock_map
    assert "requestFullscreen()" in stock_map
    assert "fullscreenchange" in stock_map
    assert 'tabindex="0"' in stock_map
    assert ".stock-map-layout" in styles
    assert "#map-container.stock-map-viewport" in styles
    assert ".stock-map-shell:fullscreen" in styles
    assert ".stock-address-modal" in styles


def test_faturado_uses_historico_style_pagination_contract():
    faturado = read("templates/pages/mov/mov-faturado.j2")
    backend = read("cde.py")
    estoque_utils = read("app/models/estoqueUtils.py")

    assert "form_endpoint=\"/logi/mov/faturado/search\"" in faturado
    assert "type=\"form\"" in faturado
    assert 'class="pagination"' in faturado
    assert "url_for('faturado', page=page-1)" in faturado
    assert "url_for('faturado', page=p)" in faturado
    assert "url_for('faturado', page=page+1)" in faturado
    assert "{{ row_count }} registros" in faturado
    assert "Nenhum resultado encontrado." in faturado
    assert "formBuscarItens" not in faturado
    assert "getElementById(\"form-field\")" not in faturado
    assert "def faturado_search()" in backend
    assert "request.args.get(\"page\", 1, type=int)" in backend
    assert "get_inv_address_with_batch_fat(page, per_page)" in backend
    assert "LIMIT ? OFFSET ?" in estoque_utils


def test_cargas_baixas_uses_historico_style_pagination_contract():
    baixas = read("templates/pages/mov/mov-carga/mov-carga-baixas.j2")
    backend = read("cde.py")

    assert "form_endpoint=\"/logi/cargas/baixas/search\"" in baixas
    assert "type=\"form\"" in baixas
    assert 'class="pagination"' in baixas
    assert "url_for('cargas_baixas', page=page-1)" in baixas
    assert "url_for('cargas_baixas', page=p)" in baixas
    assert "url_for('cargas_baixas', page=page+1)" in baixas
    assert "{{ row_count }} registros" in baixas
    assert "Nenhuma carga com baixa ou exclusão encontrada." in baixas
    assert "def cargas_baixas_search()" in backend
    assert "get_cargas_with_status(page, per_page)" in backend
    assert "def format_cargas_status(cargas)" in backend
    assert "LIMIT ? OFFSET ?" in backend


def test_dev_cargas_mock_matches_cargas_table_contract():
    backend = read("cde.py")
    cargas = read("templates/pages/mov/mov-carga/mov-carga.j2")

    for column in (
        "NRO_CARGA",
        "NRO_PEDIDO",
        "COD_CLIENTE",
        "FANT_CLIENTE",
        "OBS_CLIENTE",
        "COD_TRANSP",
        "FANT_TRANSP",
        "DT_EMISSAO",
        "DT_ENTREGA",
        "OBS_CARGA",
    ):
        assert column in backend
        assert f"columns.index('{column}')" in cargas

    assert "MOCK_CARGAS_COLUMNS" in backend
    assert "MOCK_CARGA_DETAIL_COLUMNS" in backend
    assert "MOCK_CARGA_DETAILS" in backend
    assert "LEFT JOIN DB2ADMIN.TRANSP tr" in backend
    assert "tr.FANTASIA" in backend
    assert "def mock_cargas_payload(all_cargas=False)" in backend
    assert "def mock_carga_detail_payload(id_carga)" in backend
    assert "def get_mock_carga_qtde_solic(id_carga, cod_item)" in backend
    assert "def is_mock_carga(id_carga)" in backend
    assert "modo dev sem consulta remota" in backend
    assert "if not columns and cdeapp.config.get_debug():" in backend
    assert "Usando cargas mock" in backend
    assert "Usando carga mock" in backend

    separation = read("templates/pages/mov/mov-carga/mov-carga-separacao.j2")
    separation_pending = read(
        "templates/pages/mov/mov-carga/mov-carga-separacao-pend.j2"
    )
    separation_done = read(
        "templates/pages/mov/mov-carga/mov-carga-separacao-done.j2"
    )
    incomplete = read(
        "templates/pages/mov/mov-carga/mov-carga-incompleta.j2"
    )
    cargas_js = read("static/js/lb-cargas.js")

    assert "def get_carga_info_with_carga(id_carga)" in backend
    assert "cl.OBSERVACOES" in backend
    assert "Observação do cliente:" in separation
    assert ">TRANSPORTADORA<" in separation
    assert "RECARREGAR CARGAS" in cargas
    assert 'class="carga-empty-action"' in cargas
    assert 'class="carga-ops-shell"' in incomplete
    assert 'id="cargaOpsLayout"' in incomplete
    assert ">TRANSPORTADORA<" in incomplete
    assert "Observação do cliente:" in incomplete
    assert "RETOMAR SEPARAÇÃO" in incomplete
    assert "toggleCargasRail()" in incomplete
    assert "const obsCliente" in separation_pending
    assert "const obsCliente" in separation_done
    assert 'drawObservation("OBSERVAÇÃO DO CLIENTE", obsCliente)' in cargas_js
    assert "TRANSPORTADORA:" in cargas_js

    estoque_utils = read("app/models/estoqueUtils.py")
    assert "MOCK_ITEM_LOCATIONS" in estoque_utils
    assert "def get_mock_item_inv_locations(cod_item)" in estoque_utils


def test_visual_overrides_preserve_ui_state_colors():
    styles = read("static/css/ux.css")

    assert ".navigation-bar .chevron" in styles
    assert "rotate: 0deg" in styles
    assert "td:not(.action-cell)" in styles
    assert "td.action-cell.green" in styles
    assert "td.action-cell.red" in styles
    assert "td.action-cell.blue" in styles


def test_breadcrumbs_expose_path_and_current_page():
    title_route = read("templates/components/title-route.j2")

    assert 'aria-label="Navegação estrutural"' in title_route
    assert 'aria-current="page"' in title_route
    assert "breadcrumb-home" in title_route
    assert "breadcrumb-page-id" in title_route


def test_compact_header_dividers_override_global_rule():
    styles = read("static/css/ux.css")

    assert ".titles-container .aux-buttons > hr.vert" in styles
    assert "flex: 0 0 1px" in styles
    assert "flex-wrap: wrap" in styles


def test_notification_dropdown_owns_its_visual_contract():
    styles = read("static/css/ux.css")
    script = read("static/js/script.js")

    assert "#notifications-container" in styles
    assert ".dropdown-notification-content" in styles
    assert '<strong class="dropdown-notification-title">' in script
    assert 'style="height: 16px;"' not in script


def test_system_alert_uses_visible_return_action():
    alert = read("templates/components/menus/alert.j2")
    styles = read("static/css/ux.css")

    assert 'class="system-alert-page"' in alert
    assert 'class="system-alert-card"' in alert
    assert 'class="system-alert-icon"' in alert
    assert 'class="system-alert-details"' in alert
    assert 'class="system-alert-actions"' in alert
    assert 'class="system-alert-action"' in alert
    assert "system-alert-shell" in alert
    assert "ui_icon('svg/lock.svg'" in alert
    assert 'href="{{ url_return }}"' in alert
    assert "<span>Voltar</span>" in alert
    assert "goBack()" not in alert
    assert ".system-alert-action" in styles
    assert ".system-alert-heading" in styles
    assert "width: min(560px, 100%)" in styles
    assert ".system-alert-action > span" in styles
    assert "color: #fff !important;" in styles


def test_account_and_theme_controls_live_in_expected_menus():
    navigation = read("templates/components/dropdown/dropdown-cde.j2")
    system_menu = navigation.split('id="system-menu"', 1)[1].split('id="user-menu"', 1)[0]
    user_menu = navigation.split('id="user-menu"', 1)[1]

    assert "toggleTheme()" in system_menu
    assert "theme-switch" in system_menu
    assert "cde_profile" not in system_menu
    assert "logout" not in system_menu
    assert "cde_profile" in user_menu
    assert "logout" in user_menu
    assert "navigation-actions" in navigation


def test_theme_action_dismisses_system_dropdown():
    navigation = read("templates/components/dropdown/dropdown-cde.j2")
    script = read("static/js/ui.js")
    styles = read("static/css/ux.css")

    assert "dismissDropdown(this)" in navigation
    assert "window.dismissDropdown" in script
    assert ".dropdown.is-dismissed > .dropdown-content" in styles


def test_dropdown_links_use_accent_only_on_interaction():
    styles = read("static/css/ux.css")

    assert "body.app-shell .dropdown-content a" in styles
    assert "body.app-shell .dropdown-content a:hover" in styles
    assert "body.app-shell .dropdown-content a:focus-visible" in styles


def test_navigation_and_profile_actions_use_stable_thin_arrows():
    navigation = read("templates/components/dropdown/dropdown-cde.j2")
    account = read("templates/pages/account.j2")
    component = read("templates/components/action-row.j2")
    styles = read("static/css/ux.css")

    assert "svg/bottom-point.svg" not in navigation
    assert "svg/chevron-right.svg" in navigation
    assert "action_row(" in account
    assert "profile-action-arrow" not in account
    assert "action-row-arrow" in component
    assert ".action-row:hover .action-row-arrow" in styles
    assert "transform: translateX(3px)" not in styles


def test_dark_grid_keeps_visible_contrast():
    styles = read("static/css/ux.css")

    assert "--ux-canvas-grid:" in styles
    assert "html.dark body.app-shell .view-width" in styles


def test_login_keeps_authentication_contract_inside_split_layout():
    base = read("templates/base.j2")
    login = read("templates/pages/login.j2")

    assert "block body_class" in base
    assert "login-shell" in login
    assert "login-layout" in login
    assert 'action="/login"' in login
    assert 'name="login_user"' in login
    assert 'name="password_user"' in login
    assert 'id="submitform"' in login
