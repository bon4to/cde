// JAVASCRIPT
// * métodos abrangentes do sistema


// logging dentro dos diretórios do servidor host
function logOnServer(logMessage) {
    console.log(logMessage);
    fetch('/api/log/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: logMessage })
    })
    .catch(error => {
        console.error('Erro de conexão:', error);
    });
}


// alterna os campos de acordo com a operação em (/logi/mov/)
// TODO: refatorar e modular para dentro de 'mov'
function toggleFields() {
    // obtém a operação (E, S, T, F)
    var operacao = document.getElementById('operacao').value;

    // obtém os elementos SVG
    const svgOperation = document.getElementById('svg-operation');
    const svgCfg = document.getElementById('svg-cfg');
    
    // obtém o checkbox de 'end completo'
    // * usado para movimentação de endereço completo
    var isEndCompleto = document.getElementById('is_end_completo');

    var dateFabInput = document.getElementById('date_fab');
    var cargaNumeroInput = document.getElementById('id_carga');
    var destinoNumeroInput = document.getElementById('destino_end_number');

    // remove o atributo 'required' dos campos de destino e carga
    cargaNumeroInput.removeAttribute('required');
    destinoNumeroInput.removeAttribute('required');

    // obtém os campos de data
    var EntradaFields = document.getElementById('EntradaFields');
    var FaturaFields = document.getElementById('FaturaFields');
    var TransfFields = document.getElementById('TransfFields');

    // exibe ou esconde os campos de acordo com a operação
    EntradaFields.style.display = operacao === 'E' ? 'flex' : 'none';
    FaturaFields.style.display = operacao === 'F' ? 'flex' : 'none';
    TransfFields.style.display = operacao === 'T' ? 'flex' : 'none';

    function updateSVG(operacao) {
        const svgPaths = {
            'E' : "/static/svg/arrow-down-to-dot.svg",
            'S' : "/static/svg/arrow-up-from-dot.svg",
            'T' : "/static/svg/arrow-up-down.svg",
            'F' : "/static/svg/package-check.svg"
        };

        // atualiza o SVG da operação
        svgOperation.src = svgPaths[operacao];
    }

    // atualiza o SVG da operação
    updateSVG(operacao);

    // remove o atributo 'required' do campo de data
    // * se o tipo de operação não for 'E' (entrada), não é necessário informar a data de fabricação
    if (operacao != "E") {
        dateFabInput.removeAttribute('required');
        dateFabInput.value = '';
    }

    if (operacao === 'T') {
        // adiciona o atributo 'required' ao campo de destino
        destinoNumeroInput.required = true;

        // exibe o SVG de configuração de 'movimentação de endereço completo'
        svgCfg.style.display = 'flex';
    } else if (operacao === 'F') {
        cargaNumeroInput.required = true;
        svgCfg.style.display = 'flex';
    } else { // `E` and `S`
        if (operacao === "E") {
            dateFabInput.setAttribute('required', 'true');
        }
        cargaNumeroInput.required = false;
        destinoNumeroInput.required = false;
        svgCfg.style.display = 'none';

        isEndCompleto.checked = false;
        handleCheckChange();
    }
}


// Tooltip (hover)
// * Uses 'title' attribute to show custom tooltip
document.addEventListener("mouseover", (e) => {
    // verifica se o elemento cujo mouse está sobre possui o atributo 'title'
    let title = e.target.getAttribute("title");
    if (!title) return;

    // adiciona o atributo 'data-title' ao elemento
    e.target.setAttribute("data-title", title);
    e.target.removeAttribute("title");

    // cria o tooltip
    let tooltip = document.createElement("div");
    tooltip.textContent = title;
    with (tooltip.style) {
        position =      "absolute";
        background =    "black";
        color =         "white";
        padding =       "5px";
        borderRadius =  "4px";
        fontSize =      "12px";
        whiteSpace =    "nowrap";
        pointerEvents = "none";
        zIndex =        "1000";
    }    
    document.body.appendChild(tooltip);

    // move o tooltip
    const moveTooltip = (event) => {
        tooltip.style.left = event.pageX + 10 + "px";
        tooltip.style.top = event.pageY + 10 + "px";
    };

    moveTooltip(e);
    document.addEventListener("mousemove", moveTooltip);

    // remove o tooltip
    // adiciona o atributo 'title' ao elemento novamente
    e.target.addEventListener("mouseleave", () => {
        e.target.setAttribute("title", e.target.getAttribute("data-title"));
        e.target.removeAttribute("data-title");
        tooltip.remove();
        document.removeEventListener("mousemove", moveTooltip);
    }, { once: true });
});


function handleCheckChange() {
    const checkbox     = document.getElementById('is_end_completo');
    
    const buscaField   = document.getElementById('formBuscarItens');
    const produtoField = document.getElementById('produtoField');
    const quantField   = document.getElementById('quantField');
    const qtdeInput    = document.getElementById('quantidade');
    const loteInput    = document.getElementById('lote_item');
    const itemInput    = document.getElementById('cod_item');
    
    // se for movimentação de endereço completo,
    // oculta campos desnecessários
    if (checkbox.checked) {
        qtdeInput.required = false;
        loteInput.required = false;
        itemInput.required = false;
        buscaField.classList.add('hidden');
        quantField.classList.add('hidden');
        produtoField.classList.add('hidden');

        return
    }
    qtdeInput.required = true;
    loteInput.required = true;
    itemInput.required = true;
    buscaField.classList.remove('hidden');
    quantField.classList.remove('hidden');
    produtoField.classList.remove('hidden');

    return
}


// esconde o cadeado (que indica que o campo está bloqueado)
// por id
function hideLockLabel(idLabel) {
    let label = document.getElementById(idLabel);
    label.style.opacity = '0';
}


// mostra todos os cadeados de uma vez
function showLockLabel() {
    let label1 = document.getElementById("label-cod_item");
    let label2 = document.getElementById("label-cod_lote");
    let label3 = document.getElementById("label-linha");

    if (label1) label1.style.opacity = '1';
    if (label2) label2.style.opacity = '1';
    if (label3) label3.style.opacity = '1';
}


function showLoading() {
    document.getElementById("loading-content").style.display = "block";
    document.getElementById("loading-content").style.opacity = "1";
}


function hideLoading() {
    document.getElementById("loading-content").style.opacity = "0";
    document.getElementById("loading-content").style.display = "none";
}


function confirmLogout() {
    if (confirm('Você tem certeza que deseja sair?')) {
        window.location.href = '/logout';
    }
}


// DESATIVAR LOTE
$(document).ready(function () {
    $('#desc_item').on('change', function () {
        // OBTÉM O VALOR SELECIONADO
        var selectedValue = $(this).val().toLowerCase();

        // VERIFICA SE CONTÉM 'VINHO' OU 'ESPUMANTE'
        var isVinhoSelected = selectedValue.includes('vinho');
        var isEspumanteSelected = selectedValue.includes('espumante');

        // SELECIONA INPUT-LOTE
        var inputLote = $('input[name="cod_lote"]');

        // TOGGLER
        if (isVinhoSelected || isEspumanteSelected) {
            // INPUT-LOTE -> READ-ONLY
            inputLote.prop('readonly', true);
            inputLote.val('VINHOS');
        } else {
            // LOTE -> WRITE
            inputLote.prop('readonly', false);
            inputLote.val('');
        }
    });
});


function alterarCor() {
    var elemento = document.getElementById("elemento");
    var estilo   = getComputedStyle(elemento);
  
    var corAtual = estilo.getPropertyValue("--main-color");
  
    var novaCor  = "#2688ea";
    document.documentElement.style.setProperty("--main-color", novaCor);
}


function verifyCaptcha(captcha='') {
    if (captcha == '') {
        captcha = 'CONFIRMAR';
    }
    const userInput  = prompt(`Por favor, digite ''${captcha}'' para confirmar a remoção:`);
    return userInput === captcha;
}


function maximizeText(text) {
    if (text.value != '') {
        var popupOverlay = document.createElement('div');
        var popupContent = document.createElement('div');
        var closeButton  = document.createElement('button');

        popupOverlay.className = 'popup-overlay';
        popupContent.className = 'popup-content';
        popupContent.innerHTML = '<p>' + text.value + '</p>';

        closeButton.innerHTML  = '<img class="svg-inv" src="/static/svg/xmark.svg" alt="Fechar">';
        closeButton.className  = 'btn-fancy button-mini';

        closeButton.addEventListener('click', function() {
            document.body.removeChild(popupOverlay);
        });

        popupContent.appendChild(closeButton);
        popupOverlay.appendChild(popupContent);
        document.body.appendChild(popupOverlay);
    }
}

// CHECKBOX DOWNLOAD
function toggleCheckbox(checkboxImg, checkboxInput) {
    var checkbox    = document.getElementById(checkboxInput);
    var imgCheckbox = document.getElementById(checkboxImg);

    checkbox.checked = !checkbox.checked;

    if (checkbox.checked) {
        checkbox.classList.add("checked");
    } else {
        checkbox.classList.remove("checked");
    }
}


function toggleEdit() {
    var elements = document.querySelectorAll('.hidden-button');
    elements.forEach(function(element) {
        if (element.style.display === 'table-cell') {
            element.style.display = 'none';
        } else {
            element.style.display = 'table-cell';
        }
    });
}


// FUNÇÃO PARA CAPS
function capitalizeText() {
    // para inputs
    let inputsTexto = document.querySelectorAll('input[type="text"]');
    inputsTexto.forEach(function (input) {
        input.addEventListener('input', function () {
            if (!this.classList.contains('no-uppercase')) {
                this.value = this.value.toUpperCase();
            }
        });
    });

    // para textareas que não sejam gerenciados pelo CodeMirror
    let textAreas = document.querySelectorAll('textarea');
    textAreas.forEach(function (textarea) {
        textarea.addEventListener('input', function () {
            // Ignorar textareas gerenciados pelo CodeMirror
            if (textarea.classList.contains('uppercase')) {
                this.value = this.value.toUpperCase();
            }
        });
    });
}


function toggleTable(linha) {
    let checkBox = document.getElementById("toggle_" + linha);
    let table = document.getElementById(linha + "_table");
    if (checkBox.checked == true) {
        table.style.display = "block";
    } else {
        table.style.display = "none";
    }
}


function scrollFunction() {
    var button = document.getElementById("scroll-to-top-button");
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        button.classList.remove("hidden-opacity");
    } else {
        button.classList.add("hidden-opacity");
    }
}


function scrollToTop() {
    var scrollToTopElement = document.documentElement;
    if (scrollToTopElement.scrollTop !== 0) {
        scrollToTopElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        document.body.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}


function blockImg() {
    try {
        const images = document.querySelectorAll('img');
        if (images.length > 0) {
            images.forEach(img => {
                if (img) {
                    img.setAttribute('draggable', 'false');
                }
            });
        }
    } catch (error) {
        console.error('Erro ao bloquear a arrastabilidade das imagens:', error);
    }
}


function goBack() {
    window.history.back();
}


function reloadPage() {
    location.reload();
}


function loadBase64(filePath, callback) {
    fetch(filePath)
        .then(response => response.text())
        .then(base64String => {
            callback(base64String);
        })
        .catch(error => {
            console.error('Erro ao carregar o arquivo Base64:', error);
        });
}


function getQtdeItemLS(storageKey, cod_item) {
    const storage = JSON.parse(localStorage.getItem(storageKey)) || [];
    const quantidade = storage.reduce((acc, item) => {
        if (item.cod_item === cod_item) {
            return acc + item.qtde_sep;
        }
        return acc;
    }, 0);
    return quantidade;
}


function showQuantityPopup(qtde_solic, maxEstoque, this_qtde_separada, onSubmit) {
    const popup = document.getElementById('quantityPopup');
    const obsv = document.getElementById('popupObs');
    const info = document.getElementById('popupFaltante');
    const msge = document.getElementById('popupMessage');
    const input = document.getElementById('quantityInput');
    const submitBtn = document.getElementById('submitBtn');
    const maxBtn = document.getElementById('maxBtn');

    var qtde_separada = parseInt(getQtdeItemLS(getStorageKey(), codItem), 10);
    var qtde_faltante = parseInt(qtde_solic, 10) - qtde_separada;

    msge.innerHTML = `<span class="text-main-color">${qtde_separada}</span> / ${qtde_solic}`;
    info.textContent = `(${qtde_faltante} faltante)`;
    obsv.textContent = `${maxEstoque} em estoque (${this_qtde_separada} utilizado)`;

    maxEstoque = maxEstoque - this_qtde_separada
    input.max = Math.min(qtde_faltante, maxEstoque);

    maxBtn.onclick = function() {
        input.value = input.max;
    };

    input.value = input.max;

    // verifica se o input de quantidade está satisfazendo a quantidade solicitada
    if (qtde_faltante <= 0) {
        alert(`O item ${codItem} já possui quantidade suficiente.\nRemova suas separações, caso precise substituir.`)
    } else {
        // mostra o popup
        popup.classList.remove('hidden');

        submitBtn.onclick = function() {
            const value = parseInt(input.value);

            // validacao para verificar se o input foi preenchido corretamente
            if (value > 0 && value <= input.max) {
                // oculta o popup
                popup.classList.add('hidden');
                // adiciona o item na separação
                onSubmit(value);
                // carregar totais e subtotais na tabela
                reloadItemSubtotal();
            } else {
                alert(`Por favor, insira uma quantidade válida (entre 1 e ${input.max}).`);
            }
        };
    }
}


function togglePopUp() {
    let popUp = document.getElementById('popup-field');

    if (popUp.style.display === 'flex') {
        popUp.style.display = 'none';
    } else {
        popUp.style.display = 'flex';
    }
}


function toggleTheme() {
    const root = document.documentElement;
    document.documentElement.classList.toggle('dark');

    var img = document.getElementById('toggle-theme');

    if (document.documentElement.classList.contains('dark')) {
        localStorage.setItem('theme', 'dark');
        //root.style.setProperty('--cde-color-rgb', '53, 80, 141');
        //root.style.setProperty('--logi-color-rgb', '206, 80, 34');
        //root.style.setProperty('--prod-color-rgb', '123, 104, 57');
        
        root.style.setProperty('--alt-color-1', '155, 072, 060');
        root.style.setProperty('--alt-color-2', '081, 129, 040');
        root.style.setProperty('--alt-color-3', '065, 065, 155');
        root.style.setProperty('--alt-color-4', '155, 065, -20');
        root.style.setProperty('--alt-color-5', '065, 135, 155');
        root.style.setProperty('--alt-color-6', '155, 065, 125');
        root.style.setProperty('--alt-color-7', '155, 120, 065');
    } else {
        localStorage.setItem('theme', 'light');
        //root.style.setProperty('--cde-color-rgb', '62, 94, 166');
        //root.style.setProperty('--logi-color-rgb', '234, 90, 38');
        //root.style.setProperty('--prod-color-rgb', '143, 121, 67');
        
        root.style.setProperty('--alt-color-1', ' 255, 172, 160');
        root.style.setProperty('--alt-color-2', ' 181, 229, 140');
        root.style.setProperty('--alt-color-3', ' 165, 165, 255');
        root.style.setProperty('--alt-color-4', ' 255, 165, 080');
        root.style.setProperty('--alt-color-5', ' 165, 235, 255');
        root.style.setProperty('--alt-color-6', ' 255, 165, 225');
        root.style.setProperty('--alt-color-7', ' 255, 220, 165');
    }
}


function visualDelay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function loadNotifications() {
// carrega notificacoes do backend
    fetch('/api/notification/get')
        .then(response => response.json())
        .then(data => {
            // exibe as notificacoes
            const notificationsContainer = document.getElementById('notifications-container');
            notificationsContainer.innerHTML = ''; // limpa antes de inserir
            
            let unreadNotifications = 0;
            for (let i = 0; i < data.length; i++) {
                const notification = data[i];

                // limita a exibicao de 5 notificacoes
                if (unreadNotifications >= 5) {
                    break;
                }

                // ignora as notificacoes lidas
                if (notification.flag_read) {
                    continue;
                }

                unreadNotifications++;

                // altera o icone da notificacao
                svgNotification = document.getElementById('svg-notification');
                svgNotification.src = '/static/svg/bell-dot.svg';

                // cria o elemento da notificacao
                const notificationElement = document.createElement('div');
                notificationElement.classList.add('dropdown-notification');
                notificationElement.innerHTML = `
                    <div class="flex-v" style="gap: 2px; cursor: pointer; border-bottom: 1px solid var(--light-white-h);" onclick="window.location.href='/cde/notifications/${notification.id}'">
                        <h1 class="dropdown-notification-title" style="height: 16px;">${notification.title}</h1>
                        <p class="dropdown-notification-message" style="height: 12px; margin-bottom: 4px;">${notification.message}</p>
                        <p class="dropdown-notification-date">${notification.date}</p>
                    </div>
                `;
                notificationsContainer.appendChild(notificationElement);
            }
            
            const moreElement = document.createElement('div');
            moreElement.innerHTML = `
                <div class="dropdown-notification">
                    <a style="font-family: 'Calibri', sans-serif;" href="/cde/notifications">Ver todas... (${unreadNotifications} não lidas)</a>
                </div>
            `;
            notificationsContainer.appendChild(moreElement);
        })
        .catch(error => {
            console.error('Erro ao carregar notificacoes:', error);
        });
}


function loadRecentPages() {
    // recupera o histórico do localStorage
    let recentPages = JSON.parse(localStorage.getItem('recentPages')) || [];
    recentPages.reverse(); // Inverte a ordem para exibir os itens mais recentes primeiro

    // seleciona o contêiner de botões
    let buttonsContainer = document.getElementById('recent-pages-buttons-container');
    buttonsContainer.innerHTML = ''; // Limpa os botões antes de inserir novos dados

    if (recentPages.length > 0) {
        // itera sobre o histórico e cria os botões
        recentPages.forEach(page => {
            let button = document.createElement('button'); // cria um botão para cada item
            button.classList.add('recent-page-button');
            button.textContent = page.pageId + ' | ' + page.pageName.split('(')[0];

            // adiciona o evento de clique para redirecionar para a página correspondente
            button.onclick = function() {
                window.location.href = page.pageLink;
            };

            // adiciona o botão ao contêiner
            buttonsContainer.appendChild(button);
        });
    } else {
        // se não houver páginas recentes, mostra uma mensagem
        let messageButton = document.createElement('button');
        messageButton.classList.add('recent-page-button');
        messageButton.textContent = 'Não há recentes';
        messageButton.style.cursor = 'default'; // para evitar que seja clicado

        buttonsContainer.appendChild(messageButton);
    }
}


function clearRecentPages() {
    // Remove o item "recentPages" do localStorage
    localStorage.removeItem('recentPages');

    // Limpa o conteúdo da tabela
    let table = document.getElementById('recent-pages-buttons-container');
    table.innerHTML = '';
    loadRecentPages();
}


function showToast(message, type = 'info', timer_s = 5) {
    const toastContainer = document.getElementById('toast-container');
    let icon;
    let toastColor;
    
    // validação
    if (!timer_s != 0) { timer_s = 5 }

    // conversão
    let timer_ms = timer_s * 1000;

    switch(type) {
        case 'success':
            icon = 
                `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="height: 16px; width: 16px; fill: #4CAF50;">
                <path d="M12 0C5.37258 0 0 5.37258 0 12C0 18.6274 5.37258 24 12 24C18.6274 24 24 18.6274 24 12C24 5.37258 18.6274 0 12 0ZM10.2432 16.9714L5.12034 11.8485L6.53479 10.4341L10.2432 14.1426L17.4652 6.9205L18.8797 8.33495L10.2432 16.9714Z"/>
                </svg>`;
            toastColor = '#4CAF50';
            break;
        case 'warn':
            icon = 
                `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="height: 16px; width: 16px; fill: #FF9800;">
                <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
                </svg>`;
            toastColor = '#FF9800';
            break;
        case 'error':
            icon = 
                `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="height: 16px; width: 16px; fill: #F44336;">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 13.59L16.59 17 12 12.41 7.41 17 6 15.59 10.59 11 6 6.41 7.41 5 12 9.59 16.59 5 18 6.41 13.41 11 18 15.59z"/>
                </svg>`;
            toastColor = '#F44336';
            break;
        default: // case 'info':
            icon = 
                `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="height: 16px; width: 16px; fill: #2196F3;">
                <path d="M12 0C5.37258 0 0 5.37258 0 12C0 18.6274 5.37258 24 12 24C18.6274 24 24 18.6274 24 12C24 5.37258 18.6274 0 12 0ZM13 17H11V9H13V17ZM13 7H11V5H13V7Z"/>
                </svg>`;
            toastColor = '#2196F3';
    }
    
    // cria o elemento do toast
    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.style.borderBottomColor = toastColor;
    
    // Cria o conteúdo do toast
    toast.innerHTML = `
        <div class="split-h">
            <span style="display: flex; align-items: center;">${message}</span>
            <span style="margin-left: 10px; display: flex; align-items: center;">${icon}</span>
            <span class="toast-close" style="margin-left: auto; cursor: pointer;">&times;</span>
        </div>
        <div class="toast-timer" style="background-color: ${toastColor};"></div>
    `;

    console.log("[TOAST]", message);

    // Adiciona o toast ao container
    toastContainer.appendChild(toast);

    // Configura o fechamento manual do toast
    const closeButton = toast.querySelector('.toast-close');
    closeButton.addEventListener('click', () => {
        removeToast(toast);
    });

    // Configura a animação do temporizador
    const toastTimer = toast.querySelector('.toast-timer');
    toastTimer.style.transition = `width ${timer_ms}ms linear`;
    setTimeout(() => {
        toastTimer.style.width = '0%';
    }, 50); // Pequeno atraso para iniciar a animação
    
    // Define a duração do toast
    setTimeout(() => {
        removeToast(toast);
    }, timer_ms);
}


function removeToast(toast) {
    toast.classList.remove('show');
    toast.classList.add('hide');
    
    // Remove o toast do container após o tempo especificado
    setTimeout(() => {
        toast.remove();
    }, 500);
}


window.addEventListener("load", function() {
    hideLoading();
});


window.onload = function () {
    capitalizeText();
    blockImg();
    try {
        updateFilterIndex();
    } catch (error) {
        console.log('[INFO] lb-filter: A rota não contém filtros.');
    }
    try {
        toggleContainer();
    } catch (error) {
        console.log('[INFO] lb-float: A rota não contém float-container.');
    }
    try {
        loadNotifications();
    } catch (error) {
        console.log('[INFO] A rota não contém dropdown de notificação.');
    }
    hideLoading();
};


window.onscroll = function() {
    scrollFunction();
};