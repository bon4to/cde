// JAVASCRIPT


// CAMPOS DE TRANSFERENCIA
function toggleFields() {
    var operacao = document.getElementById('operacao').value;
    const svgImage = document.getElementById('svg-image');
    const svgCfg = document.getElementById('svg-cfg');
    
    var is_end_completo = document.getElementById('is_end_completo');

    var destinoFields = document.getElementById('destinoFields');
    var destinoNumeroInput = document.getElementById('destino_end_number');
    
    var cargaFields = document.getElementById('cargaFields');
    var cargaNumeroInput = document.getElementById('id_carga');

    destinoNumeroInput.removeAttribute('required');
    cargaNumeroInput.removeAttribute('required');

    destinoFields.style.display = operacao === 'T' ? 'contents' : 'none';
    cargaFields.style.display = operacao === 'F' ? 'contents' : 'none';

    const svgPaths = {
        'E' : "/static/svg/arrow-down-to-dot.svg",
        'S' : "/static/svg/arrow-up-from-dot.svg",
        'T' : "/static/svg/arrow-down-up.svg",
        'F' : "/static/svg/package-check.svg"
    };

    svgImage.src = svgPaths[operacao];
    
    if (operacao === 'T') {
        destinoNumeroInput.required = true;
        svgCfg.style.display = 'flex';
    } else if (operacao === 'F') {
        cargaNumeroInput.required = true;
        svgCfg.style.display = 'flex';
    } else {
        cargaNumeroInput.required = false;
        destinoNumeroInput.required = false;
        svgCfg.style.display = 'none';

        is_end_completo.checked = false;
        handleCheckChange();
    }
}

function handleCheckChange() {
    const checkbox = document.getElementById('is_end_completo');
    const quantField = document.getElementById('quantField');
    const produtoField = document.getElementById('produtoField');
    const busca = document.getElementById('formBuscarItens');
    const quantidade = document.getElementById('quantidade');
    const cod_lote = document.getElementById('lote_item');
    const cod_item = document.getElementById('cod_item');
    
    if (checkbox.checked) {
        produtoField.style.display = 'none';
        busca.style.display = 'none';
        quantField.style.display = 'none';
        quantidade.required = false;
        cod_lote.required = false;
        cod_item.required = false;
    } else {
        produtoField.style.display = 'block';
        busca.style.display = 'block';
        quantField.style.display = 'block';
        quantidade.required = true;
        cod_lote.required = true;
        cod_item.required = true;
    }
}

// VISUAL DE CADEADOS
function lockIcoHide(idLabel) {
    let label = document.getElementById(idLabel);
    label.style.opacity = '0';
}

// VISUAL DE CADEADOS
function lockIcoShow() {
    let label2 = document.getElementById("label-cod_item");
    let label3 = document.getElementById("label-linha");

    label2.style.opacity = '1';
    label3.style.opacity = '1';

    let label1 = document.getElementById("label-cod_lote");
    label1.style.opacity = '1';
}

function showLoading() {
    document.getElementById("loading-content").style.display = "fixed";
    document.getElementById("loading-content").style.opacity = "1";

}

function hideLoading() {
    document.getElementById("loading-content").style.display = "none";
    document.getElementById("loading-content").style.opacity = "0";
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
            inputLote.val('VINHO');
        } else {
            // LOTE -> WRITE
            inputLote.prop('readonly', false);
            inputLote.val('');
        }
    });
});

function alterarCor() {
    var elemento = document.getElementById("elemento");
    var estilo = getComputedStyle(elemento);
  
    var corAtual = estilo.getPropertyValue("--cor-destaque");
  
    var novaCor = "#2688ea";
    document.documentElement.style.setProperty("--cor-destaque", novaCor);
}


function maximizeText(text) {
    if (text.value != '') {
        var popupOverlay = document.createElement('div');
        popupOverlay.className = 'popup-overlay';

        var popupContent = document.createElement('div');
        popupContent.className = 'popup-content';
        popupContent.innerHTML = '<p>' + text.value + '</p>';

        var closeButton = document.createElement('button');
        closeButton.innerText = '×';
        closeButton.className = 'btn-fancy button-mini';
        closeButton.addEventListener('click', function() {
            document.body.removeChild(popupOverlay);
        });

        popupContent.appendChild(closeButton);
        popupOverlay.appendChild(popupContent);
        document.body.appendChild(popupOverlay);
    }
    
}

// HEADER POP-UP
window.addEventListener('scroll', function () {
    // ENCONTRA A POSIÇÃO Y = VERTICAL
    var scrollPosition = window.scrollY || document.documentElement.scrollTop;

    if (scrollPosition > 50) {
        // CALCULA O VALOR CONFORME O SCROLL (10 COMO MINIMO)
        var blurValue = Math.min(scrollPosition / 10, 10);
        // APLICA
        document.querySelector('header.main-header').classList.add('scrolled');
        document.querySelector('div.user-button').classList.add('scrolled');
        document.querySelector('p.user-name').classList.add('scrolled');
        document.querySelector('div.user-name').classList.add('scrolled');
        document.querySelector('div.user-logger').classList.add('scrolled');

    } else {
        document.querySelector('header.main-header').classList.remove('scrolled');
        document.querySelector('div.user-button').classList.remove('scrolled');
        document.querySelector('p.user-name').classList.remove('scrolled');
        document.querySelector('div.user-name').classList.remove('scrolled');
        document.querySelector('div.user-logger').classList.remove('scrolled');
    }
});


// CHECKBOX DOWNLOAD
function toggleCheckbox(placebo, checkbox) {
    var checkbox = document.getElementById(checkbox);
    var imgCheckbox = document.getElementById(placebo);

    checkbox.checked = !checkbox.checked;

    if (checkbox.checked) {
        imgCheckbox.classList.add("checked");
    } else {
        imgCheckbox.classList.remove("checked");
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
function capitalizeTexto() {

    let inputsTexto = document.querySelectorAll('input[type="text"]');
    inputsTexto.forEach(function (input) {
        input.addEventListener('input', function () {

            this.value = this.value.toUpperCase();
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
        button.classList.remove("hidden");
    } else {
        button.classList.add("hidden");
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


function togglePopUp() {
    let popUp = document.getElementById('popup-field');

    if (popUp.style.display === 'flex') {
        popUp.style.display = 'none';
    } else {
        popUp.style.display = 'flex';
    }
}

const toggleTheme = document.getElementById('toggle-theme');
toggleTheme.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');

    if (document.body.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark');
    } else {
        localStorage.setItem('theme', 'light');
    }
});

window.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
});


window.addEventListener("load", function() {
    hideLoading();
});

window.onload = function () {
    capitalizeTexto();
    blockImg();
    updateFilterIndex();
    toggleContainer();
    hideLoading();

};

window.onscroll = function() {
    scrollFunction();
};