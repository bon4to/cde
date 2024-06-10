// lb-float-cont por Lucas Bonato
// versão: v1.9


var suplementstat_fc = ("Suplemento: [lb-float-cont v1.8]: ");

// console.log(suplementstat_fc + "Iniciando...");
// LISTENERS
var offsetX, offsetY, isDragging = true, isFixed = true;
var container = document.getElementById('floating-container');
var fixMoveBtn = document.getElementById('fix-move-btn');

if (container) {
    container.addEventListener('mousedown', startDragging);
    container.addEventListener('touchstart', startDragging);

    document.addEventListener('mousemove', drag);
    document.addEventListener('touchmove', drag);

    document.addEventListener('mouseup', stopDragging);
    document.addEventListener('touchend', stopDragging);
}
// console.log(suplementstat_fc + "Iniciado com sucesso. Pronto para ser utilizado.");

// CONTAINER FLUTUANTE
function toggleContainer() {
    var container = document.getElementById('floating-container');
    if (container) {
        container.classList.toggle('show');
        try {
            document.getElementById("input_code").focus();
        } catch (error) {
            console.info('O campo flutuante não existe:', error)
        }
        // console.log(suplementstat_fc + "O container foi inicializado para uso.");
    } else {
        // console.log(suplementstat_fc + "O elemento 'floating-container' não foi encontrado.");
    }
}


function closeContainer() {
    var container = document.getElementById('floating-container');
    // console.log(suplementstat_fc + "O container foi ocultado.");
    container.classList.remove('show');
}

function stopDragging() {
    isDragging = false;
}

function toggleFixMove() {
    var container = document.getElementById('floating-container');
    var tablesContainer = document.querySelector('.tables-container');

    container.classList.toggle('absolute');
    tablesContainer.classList.toggle('absolute');

    isFixed = !isFixed;

    if (isFixed) {
        container.style.left = '';
        container.style.top = '';
        container.style.right = '';
        container.style.bottom = '';

        container.style.scale = '1';
        container.style.transition = 'scale 0.2s ease';

        container.style.position = 'relative';
        container.style.zIndex = '998';

        fixMoveBtn.style.transform = 'scaleX(-1)';
        //// console.log(suplementstat_fc + "O container foi bloqueado para movimento.");

    } else {
        container.style.left = '';
        container.style.top = '';
        container.style.right = '';
        container.style.bottom = '';

        container.style.scale = '1.03';
        container.style.transition = 'scale 0.2s ease';

        container.style.position = 'absolute';
        container.style.zIndex = '1099';

        fixMoveBtn.style.transform = 'scaleX(1)';
        //// console.log(suplementstat_fc + "O container foi liberado para movimento.");

    }

}


function startDragging(e) {
    if (e.target.tagName.toLowerCase() === 'select'|| e.target.tagName.toLowerCase() === 'input'|| e.target.tagName.toLowerCase() === 'button') {
        return;
    }

    isDragging = true;

    if (e.type === 'mousedown') {
        offsetX = e.clientX - container.getBoundingClientRect().left;
        offsetY = e.clientY - container.getBoundingClientRect().top;
    } else if (e.type === 'touchstart' && e.touches.length === 1) {
        offsetX = e.touches[0].clientX - container.getBoundingClientRect().left;
        offsetY = e.touches[0].clientY - container.getBoundingClientRect().top;
    }
}

function drag(e) {
    if (!isDragging || isFixed) return;
    e.preventDefault();

    var containerRect = container.getBoundingClientRect();
    var windowWidth = window.innerWidth - 40;
    var windowHeight = window.innerHeight;

    if (e.type === 'mousemove') {
        var newLeft = e.clientX - offsetX;
        var newTop = e.clientY - offsetY;

        // Verificar os limites da janela
        if (newLeft < 0) {
            newLeft = 0;
        } else if (newLeft + containerRect.width > windowWidth) {
            newLeft = windowWidth - containerRect.width;
        }

        if (newTop < 0) {
            newTop = 0;
        } else if (newTop + containerRect.height > windowHeight) {
            newTop = windowHeight - containerRect.height;
        }

        container.style.left = newLeft + 'px';
        container.style.top = newTop + 'px';
    } else if (e.type === 'touchmove' && e.touches.length === 1) {
        var newLeft = e.touches[0].clientX - offsetX;
        var newTop = e.touches[0].clientY - offsetY;

        // Verificar os limites da janela
        if (newLeft < 0) {
            newLeft = 0;
        } else if (newLeft + containerRect.width > windowWidth) {
            newLeft = windowWidth - containerRect.width;
        }

        if (newTop < 0) {
            newTop = 0;
        } else if (newTop + containerRect.height > windowHeight) {
            newTop = windowHeight - containerRect.height;
        }

        container.style.left = newLeft + 'px';
        container.style.top = newTop + 'px';
    }
}
