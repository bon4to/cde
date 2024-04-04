// JAVASCRIPT


// CAMPOS DE TRANSFERENCIA
function toggleFields() {
    var operacao = document.getElementById('operacao').value;
    var destinoFields = document.getElementById('destinoFields');
    var destinoNumeroInput = document.getElementById('destino_numero');

    destinoFields.style.display = operacao === 'transferencia' ? 'block' : 'none';
    destinoNumeroInput.required = operacao === 'transferencia';
}

// VISUAL DE CADEADOS
function lockIcoHide(idLabel) {
    let label = document.getElementById(idLabel);
    label.style.opacity = '0';
}

// VISUAL DE CADEADOS
function lockIcoShow() {
    let label2 = document.getElementById("label-sku");
    let label3 = document.getElementById("label-linha");

    label2.style.opacity = '1';
    label3.style.opacity = '1';

    let label1 = document.getElementById("label-lote");
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
    $('#produto').on('change', function () {
        // OBTÉM O VALOR SELECIONADO
        var selectedValue = $(this).val().toLowerCase();

        // VERIFICA SE CONTÉM 'VINHO' OU 'ESPUMANTE'
        var isVinhoSelected = selectedValue.includes('vinho');
        var isEspumanteSelected = selectedValue.includes('espumante');

        // SELECIONA INPUT-LOTE
        var inputLote = $('input[name="lote"]');

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
function toggleCheckbox() {
    let checkbox = document.getElementById("img_download");
    let imgCheckbox = document.getElementById("img_checkbox");

    checkbox.checked = !checkbox.checked;

    if (checkbox.checked) {
        imgCheckbox.classList.add("checked");
    } else {
        imgCheckbox.classList.remove("checked");
    }
}

function toggleEdit() {
    var elements = document.querySelectorAll('.svg-link');
    elements.forEach(function(element) {
        if (element.style.display === 'unset') {
            element.style.display = 'none';
        } else {
            element.style.display = 'unset';
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

window.addEventListener("load", function() {
  hideLoading();
});

window.onload = function () {
    capitalizeTexto();
    toggleContainer();
    updateFilterIndex();
    hideLoading();
};
