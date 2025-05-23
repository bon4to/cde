// lb-cargas.js

let headerMainLogo;

var itemCount = 0;

if (nroCarga != '') {
    reloadItemSubtotal();
}


function getStorageKey() {
    // retorna a chave do localStorage para a separação da carga
    // parsificada por 'nroCarga'
    // (ex.: 'separacao-carga-123')
    return `separacao-carga-${nroCarga}`;
}


function updateItemCount(itemCount) {
    // atualiza o contador de itens do 'cart'
    document.querySelector('.item-count').textContent = itemCount;
}


function preQuickRouting(routePage) {
    const navigatorInput = document.getElementById('navigatorInput');
    const headerInput = document.getElementById('headerInput');

    var idForRoute;
    try {
        // Se um dos inputs tiver valor, preencha o outro
        if (navigatorInput.value) {
            idForRoute = navigatorInput.value;
        } else if (headerInput.value) {
            idForRoute = headerInput.value;
        }
        idForRoute = parseInt(idForRoute);
        // Expressão para validar números inteiros ou com sufixos como -1, -2, -3...
        const regex = /^-?\d+(-\d+)?$/;

        // Verifica se o input de requisição foi preenchido corretamente
        if (!regex.test(idForRoute)) {
            showToast('Por favor, insira um número válido (ex: 123 ou 123-1).', 2);
            return
        } 
        redirectQuickRouting(routePage, idForRoute);
        
    } catch (error) {
        console.error(error);
    }
}


function redirectQuickRouting(routePage, nroCarga) {
    // redireciona para a rota informada
    const url = `/logi/${routePage}/${nroCarga}`;
    window.location.href = url;
}


function listSeparationsLocalStorage(routePage) {
    // limpa a tabela atual, evitando duplicações e dados desatualizados
    const allSeparationsTable = document.getElementById('allSeparationsTable').getElementsByTagName('tbody')[0];

    // Verifica se a URL da página corresponde à rota "/mov/carga/incompleta"
    if (window.location.pathname == '/logi/cargas/incompletas/') {
        return;
    }
    allSeparationsTable.innerHTML = '';

    // obtem todas as chaves (de carga) armazenadas no localStorage
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('separacao-carga-')) {
            keys.push(key);
        }
    }

    // ordena as chaves em ordem decrescente
    keys.sort((a, b) => b.localeCompare(a));


    // se nenhuma separação foi iniciada, adiciona uma linha
    if (keys.length == 0) {
        const row = allSeparationsTable.insertRow();
        row.insertCell(0).textContent = 'Nenhuma separação iniciada';
    }

    let activeRow = null;

    // remove prefixo 'separacao-carga-'
    // percorre as chaves e adiciona as linhas na tabela
    keys.forEach(key => {
        const cargaNumber = key.replace('separacao-carga-', '');
        const row = allSeparationsTable.insertRow();
        row.insertCell(0).textContent = cargaNumber;
        row.classList.add("selectable-row");

        if (cargaNumber === nroCarga) {
            row.classList.add("active");
            activeRow = row;
        } 

        row.addEventListener('click', function() {
            window.location.href = `/mov/${routePage}/${cargaNumber}`;
        });
    });

    if (activeRow && nroCarga != '0') {
        activeRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}


async function getSeparadorName(user_id) {
    let separador = document.getElementById('separador-info');

    try {
        const response = await fetch(`/get/username/${user_id}`);
        const data = await response.json();
        username = data.username;
    } catch (error) {
        console.error('Erro ao obter separador:', error);
        username = "(indefinido)";
    }

    separador.innerText = username;
}


async function genCargaReport() {
    const { jsPDF } = window.jspdf;
    const report    = new jsPDF();
    const tableData = [];
    const rows      = document.querySelectorAll("#itemsTable tbody tr");
    const userName  = document.getElementById('separador-info').innerText;
    
    // Seleciona o botão de finalizar separação.
    const btnGenCargaReport = document.getElementById('btnGenCargaReport');
    
    // Exibe um indicador de carregamento e desativa o botão de finalizar.
    btnGenCargaReport.onclick = '';
    btnGenCargaReport.innerHTML = '<span class="loader-inline"></span>';
    
    await visualDelay(700);
    
    try {
        rows.forEach(row => {
            const rowData = [];
            row.querySelectorAll("td").forEach(cell => {
                rowData.push(cell.innerText);
            });
            tableData.push(rowData);
        });

        const columns = ["Endereço", "Item (Código)", "Item (Descrição)", "Lote (Código)", "Qtde (Sep.)"];

        const data = tableData.map(row => ({
            rua_letra_end : row[0],
            cod_item      : row[1],
            desc_item     : row[2],
            lote_item     : row[3],
            qtde_solic    : row[4]
        }));

        const filteredData = data.filter(item => !item.lote_item.startsWith('Subtotal:'));
        const totalQtdeSolic = filteredData.reduce((total, item) => total + parseFloat(item.qtde_solic), 0);

        data.push({
            rua_letra_end : '',
            cod_item      : '',
            desc_item     : '',
            lote_item     : 'Total:',
            qtde_solic    : totalQtdeSolic
        });

        let startY         = 48;
        var cellHeight     = 10;
        const cellPadding  = 4;

        const startX       = 10;
        const marginBottom = 20;
        const colWidths    = [25, 30, 80, 30, 25];
        const pageHeight   = report.internal.pageSize.height;

        const drawHeader = () => {
            report.addImage(headerMainLogo, 'PNG', 164, 20, 35, 8);

            report.setFont("times", "bold");
            report.setFontSize(16);
            report.text("Relatório de Carga", 10, 22);

            report.setFont("times", "normal");
            report.setFontSize(12);
            report.text("INDUSTRIA DE SUCOS 4 LEGUA LTDA - EM RECUPERACAO JUDICIAL", 10, 28);

            report.setDrawColor(192, 192, 192);
            report.setLineWidth(0.2);
            report.line(10, 32, 200, 32);
            report.setDrawColor(0, 0, 0);

            report.setFontSize(10);

            if (typeof fantCliente !== 'undefined') {
                report.setFont("times", "bold");
                report.text(`CLIENTE: ${fantCliente}`, 10, 38);
            }
            
            if (typeof nroCarga !== 'undefined') {
                report.setFont("times", "normal");
                report.text(`CARGA: ${nroCarga}`, 10, 42);
            }
            report.setDrawColor(192, 192, 192);
        };

        const drawFooter = () => {
            const currentDateTime = new Date().toLocaleString();
            const totalPages      = report.getNumberOfPages();

            for (let i = 1; i <= totalPages; i++) {
                report.setPage(i);
                const pageNumber = report.internal.getCurrentPageInfo().pageNumber;

                report.setDrawColor(192, 192, 192);
                report.setLineWidth(0.2);
                report.line(10, pageHeight - marginBottom, 200, pageHeight - marginBottom);
                report.setDrawColor(0, 0, 0);

                report.setFontSize(10);
                if (typeof userName === 'string') {
                    report.text(userName, 10, pageHeight - 10, { align: 'left' });
                }

                report.text(`${pageNumber} / ${totalPages}`, report.internal.pageSize.width / 2, pageHeight - 10, { align: 'center' });

                if (typeof currentDateTime === 'string') {
                    report.text(currentDateTime, report.internal.pageSize.width - 10, pageHeight - 10, { align: 'right' });
                }
            }
        };

        const drawTable = (data) => {
            // Desenhando cabeçalho da tabela
            report.setFontSize(10);
            report.setLineWidth(0.1);
            report.setFont("times", "bold");
            columns.forEach((col, i) => {
                const x = startX + colWidths.slice(0, i).reduce((a, b) => a + b, 0);
                report.setFillColor(62, 94, 166);
                report.setTextColor(255, 255, 255);
                report.rect(x, startY, colWidths[i], cellHeight, 'F');
                report.text(col, x + cellPadding, startY + cellHeight / 2 + cellPadding / 2);
            });
            report.setTextColor(20, 20, 20);
            report.setDrawColor(220, 220, 220);

            // Ajustando a posição Y após o cabeçalho
            startY += cellHeight;
            report.setFont("times", "normal");

            // Desenhando linhas da tabela
            data.forEach((item) => {
                const row = [
                    item.rua_letra_end,
                    item.cod_item,
                    item.desc_item,
                    item.lote_item,
                    item.qtde_solic.toString()
                ];

                const isSubtotal = item.lote_item && item.lote_item.startsWith('Subtotal:');
                const isTotal    = item.lote_item === 'Total:';

                const descLines = report.splitTextToSize(item.desc_item, colWidths[2] - 2 * cellPadding);
                const cellLines = Math.max(descLines.length, 1);
                var currentCellHeight = cellHeight;

                if (cellLines > 2) {
                    currentCellHeight = 14;
                }

                row.forEach((cell, i) => {
                    const x = startX + colWidths.slice(0, i).reduce((a, b) => a + b, 0);
                    const y = startY;

                    if (isSubtotal) {
                        report.setFillColor(220, 220, 220); 
                        report.setFont("times", "bold");
                    } else if (isTotal) {
                        report.setFillColor(192, 192, 192); 
                        report.setDrawColor(192, 192, 192); 
                        report.setFont("times", "bold");
                    } else {
                        report.setFillColor(255, 255, 255); 
                        report.setFont("times", "normal");
                    }

                    report.rect(x, y, colWidths[i], currentCellHeight, 'F');
                    const text = report.splitTextToSize(cell, colWidths[i] - 2 * cellPadding);
                    report.text(text, x + cellPadding, y + cellPadding);
                    report.setFillColor(50, 50, 50);
                    report.rect(x, y, colWidths[i], currentCellHeight, 'S');
                });

                startY += currentCellHeight;

                if (startY + cellHeight + marginBottom > pageHeight) {
                    report.addPage();
                    drawHeader();
                    startY = 50;
                    report.setFontSize(10);
                    report.setLineWidth(0.1);
                }
            });
        };

        loadBase64('/static/b64/cde-logo-b.txt', function(base64String) {
            headerMainLogo = base64String; // Atribuir ao escopo global
            drawHeader();
            drawTable(data);
            drawFooter(report.internal.getNumberOfPages());

            if (typeof obs_carga !== 'undefined' && obs_carga.trim().length > 0) {
                const finalY = startY + 10;
                report.setFontSize(10);
                report.setFont("times", "bold");
                report.text("OBSERVACÃO: ", 10, finalY);

                report.setFont("times", "normal");
                report.text(obs_carga, 10 + report.getTextWidth("OBSERVACÃO:") + 5, finalY);
            }

            const pdfName = `MOV006-CG${nroCarga}.pdf`;
            report.save(pdfName);
            btnGenCargaReport.innerHTML = `✓`;
            btnGenCargaReport.classList.add('disabled');
        });
    } catch (error) {
        console.error('Erro ao gerar relatório:', error);
        btnGenCargaReport.innerHTML = `✘`;
        btnGenCargaReport.classList.add('disabled');
    }
}


function toggleCart() {
    const cartDropdown = document.getElementById('cart-dropdown');
    const itemsCountElement = document.querySelector('.item-count');
    const itemsCount = parseInt(itemsCountElement.textContent, 10);

    if (itemsCount > 0) {
        cartDropdown.classList.toggle('hidden');

        if (!cartDropdown.classList.contains('hidden')) {
            renderCartSubtotals();
        }
    }
}


function renderSubtotals() {
    const subtotalsTable = document.getElementById('subtotalsTable').getElementsByTagName('tbody')[0];
    subtotalsTable.innerHTML = '';

    getSeparacao().then(sepCarga => {        
        let subtotals = {};

        sepCarga.forEach(item => {
            if (subtotals[item.cod_item]) {
                subtotals[item.cod_item] += item.qtde_sep;
            } else {
                subtotals[item.cod_item] = item.qtde_sep;
            }
        });

        for (const [cod_item, subtotal] of Object.entries(subtotals)) {
            const row = subtotalsTable.insertRow();
            row.insertCell(0).textContent = cod_item;
            row.insertCell(1).textContent = subtotal;
        }
    })
    .catch(error => {
        console.log('A separação foi finalizada.', error);
    });
}


function listSeparationsFromServer(routePage, reportDir='cargas') {
    const payload = {
        report_dir: reportDir
    };
    fetch('/get/list-all-separations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
    .then(response => response.json())
    .then(files => {
        const tableBody = document.getElementById('allSeparationsTable').getElementsByTagName('tbody')[0];
        tableBody.innerHTML = '';

        let activeRow = null;

        if (files.error) {
            const row = tableBody.insertRow();
            const cell = row.insertCell(0);
            cell.colSpan = 1;
            cell.textContent = files.error;
        } else {
            files.forEach(file => {
                const cargaNumber = file.replace('separacao-carga-', '').replace('.json', '');
                const row = tableBody.insertRow();
                const cell = row.insertCell(0);
                cell.textContent = cargaNumber;
                row.classList.add("selectable-row");

                if (cargaNumber === nroCarga) {
                    row.classList.add("active");
                    activeRow = row;
                } 

                row.addEventListener('click', function() {
                    window.location.href = `/logi/${routePage}/${cargaNumber}`;
                });
            });
            if (activeRow && nroCarga != '0') {
                activeRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    })
    .catch(error => {
        console.error('Erro ao carregar dados do servidor:', error);
    });
}


function clearAllSeparations() {
    const confirmation = confirm('Você tem certeza que deseja limpar TODAS as separações? Esta ação não pode ser desfeita.');
    if (confirmation) {
        if (!verifyCaptcha()) {
            alert('O captcha foi cancelado ou preenchido incorretamente.')
        } else {
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key.startsWith('separacao-carga-')) {
                    localStorage.removeItem(key);
                }
            }
            reloadTables();
            alert('Operação concluída.');
        }
    }
}


async function toggleDoneCarga() {
    try {
        const concludeResponse = await fetch(`/api/conclude-carga/${nroCarga}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        const concludeData = await concludeResponse.json();

        if (concludeData.success) {
            showToast('Carga removida com sucesso.', 'success', 10);
            // recarregar a tabela
            document.getElementById('cargaContainer').innerHTML = `
            <div style="display: flex; justify-content: center; height: 100%;">
                <p class="disabled">
                    Carga removida com sucesso.
                </p>
            </div>
            `;
            stockTable = document.getElementById('stockTable')
            if (stockTable) stockTable.style.display = 'none';
        } else {
            showToast(`<details><summary>Erro ao remover a carga:</summary> ${concludeData.error}</details>`, 'error', 10);
            return;
        }
    } catch (error) {
        console.error('Erro ao remover a carga:', error);
        showToast(`<details><summary>Erro ao remover a carga:</summary> ${error}</details>`, 'error', 10);
        return; // Aborta o processo se houver erro
    }
}


async function toggleDoneCargaIncompleta() {
    try {
        const concludeResponse = await fetch(`/api/conclude-incomp/${nroCarga}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        const concludeData = await concludeResponse.json();

        if (concludeData.success) {
            showToast('Pendência da carga removida com sucesso.', 'success', 10);
            // recarregar a tabela
            document.getElementById('incompTable').innerHTML = `
            <div style="display: flex; justify-content: center; height: 100%;">
                <p class="disabled">
                    Pendência da carga removida com sucesso.
                </p>
            </div>
            `;
            stockTable = document.getElementById('stockTable')
            if (stockTable) stockTable.style.display = 'none';
        } else {
            showToast(`<details><summary>Erro ao remover pendência da carga incompleta:</summary> ${concludeData.error}</details>`, 'error', 10);
            return;
        }
    } catch (error) {
        console.error('Erro ao remover pendência da carga incompleta:', error);
        showToast(`<details><summary>Erro ao remover pendência da carga incompleta:</summary> ${error}</details>`, 'error', 10);
        return; // Aborta o processo se houver erro
    }
}


function excludeCarga() {
    const confirmation = confirm('Você tem certeza que deseja limpar TODOS os itens desta carga? Esta ação não pode ser desfeita.');
    if (confirmation) {
        if (!verifyCaptcha(nroCarga)) {
            showToast('O captcha foi cancelado ou preenchido incorretamente.', 'error', 10);
            return;
        }
        toggleDoneCarga();
    }
}


function excludeCargaIncompleta() {
    const confirmation = confirm('Você tem certeza que deseja limpar TODOS os itens incompletos? Esta ação não pode ser desfeita.');
    if (confirmation) {
        if (!verifyCaptcha(nroCarga)) {
            showToast('O captcha foi cancelado ou preenchido incorretamente.', 'error', 10);
            return;
        }
        toggleDoneCargaIncompleta();
    }
}


function renderCartSubtotals() {
    const cartItemsContainer = document.querySelector('.cart-items');
    cartItemsContainer.innerHTML = '';

    getSeparacao().then(sepCarga => {
        let subtotals = {};

        sepCarga.forEach(item => {
            if (subtotals[item.cod_item]) {
                subtotals[item.cod_item] += item.qtde_sep;
            } else {
                subtotals[item.cod_item] = item.qtde_sep;
            }
        });

        const sortedEntries = Object.entries(subtotals).sort((a, b) => {
            const codA = a[0].toUpperCase();
            const codB = b[0].toUpperCase();

            if (codA < codB) {
                return -1;
            }
            if (codA > codB) {
                return 1;
            }
            return 0;
        });

        let itemCount = 0;

        sortedEntries.forEach(([cod_item, subtotal]) => {
            const listItem = document.createElement('li');
            listItem.classList.add('cart-item');
            listItem.innerHTML = `
                <span class="item-name">${cod_item} |</span>
                <span class="item-quantity text-main-color">${subtotal}</span>
            `;
            cartItemsContainer.appendChild(listItem);
            itemCount += 1;

            updateItemSubtotal(cod_item, subtotal)
        });
        
        updateItemCount(itemCount);
    }).catch(error => {
        console.log('A separação foi finalizada.', error);
    });
}


function reloadItemSubtotal() {
    getSeparacao().then(sepCarga => {
        let subtotals = {};

        sepCarga.forEach(item => {
            if (subtotals[item.cod_item]) {
                subtotals[item.cod_item] += item.qtde_sep;
            } else {
                subtotals[item.cod_item] = item.qtde_sep;
            }
        });

        const sortedEntries = Object.entries(subtotals).sort((a, b) => {
            const codA = a[0].toUpperCase();
            const codB = b[0].toUpperCase();

            if (codA < codB) {
                return -1;
            }
            if (codA > codB) {
                return 1;
            }
            return 0;
        });
        
        sortedEntries.forEach(([cod_item, subtotal]) => {
            updateItemSubtotal(cod_item, subtotal);
        });
    });
}


function updateItemSubtotal(cod_item, subtotal) {
    const row = document.querySelector(`tr[data-cod-item="${cod_item}"]`);
    if (row) {
        let subtotalCell = row.querySelector('.subtotal-cell');
        if (!subtotalCell) {
            subtotalCell = document.createElement('td');
            subtotalCell.classList.add('subtotal-cell');
            row.appendChild(subtotalCell);
        }
        subtotalCell.textContent = subtotal;
    }
}


function removeItem(index) {
    const confirmation = confirm('Você tem certeza que deseja remover este item?');
    if (confirmation) {
        let sepCarga = JSON.parse(localStorage.getItem(getStorageKey())) || [];
        sepCarga.splice(index, 1);
        localStorage.setItem(getStorageKey(), JSON.stringify(sepCarga));
        renderItems();
    }
}


function clearItems() {
    const confirmation = confirm(`Você tem certeza que deseja limpar a separacao de ${nroCarga}?`);
    if (confirmation) {
        localStorage.removeItem(getStorageKey());
        renderItems();
    }
}


function saveIntoServer(data, filename, reportDir='cargas') {
    const payload = {
        data: data,
        filename: filename,
        report_dir: reportDir
    };

    fetch('/post/save-localstorage', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
    .then(response => response.json())
    .then(result => {
        console.log('Dados enviados com sucesso:', result);
    })
    .catch(error => {
        console.error('Erro ao enviar dados para o servidor:', error);
    });
}


function getQtdeItemEnderecoLS(storageKey, cod_item, nroCarga, lote_item, rua_letra, rua_numero) {
    const storage = JSON.parse(localStorage.getItem(storageKey)) || [];
    const quantidade = storage.reduce((acc, item) => {
        if (
          item.cod_item === cod_item && 
          item.rua_letra === rua_letra && 
          item.rua_numero === rua_numero && 
          item.lote_item === lote_item 
        ) {
            return acc + item.qtde_sep;
        }
        return acc;
    }, 0);
    return quantidade;
}


function pushItemIntoSeparacao(maxEstoque, qtdeSolic, address, lote_item) {
    const [rua_letra, rua_numero] = address.split('.');
    var this_qtde_separada = getQtdeItemEnderecoLS(getStorageKey(), codItem, nroCarga, lote_item, rua_letra, rua_numero);
    showQuantityPopup(qtdeSolic, maxEstoque, this_qtde_separada, function(value) {
        showLoading();
        addItem(nroCarga, codItem, lote_item, rua_letra, rua_numero, value);
        hideLoading();
    });
}


function addItem(nrocarga, cod_item, lote_item, rua_letra, rua_numero, qtde_sep) {
    let sepCarga = JSON.parse(localStorage.getItem(getStorageKey())) || [];
    let user_id = userID
    let item = { nrocarga, cod_item, lote_item, rua_letra, rua_numero, qtde_sep, user_id };
    sepCarga.push(item);
    localStorage.setItem(getStorageKey(), JSON.stringify(sepCarga));
}


function hidePopUp() {
    const popup = document.getElementById('quantityPopup');
    popup.classList.add('hidden');
}


async function fetchQtdeSolic(id_carga, cod_item, isTotal=0) {
    try {
        const response = await fetch(`/api/carga/qtde_solic?id_carga=${id_carga}&cod_item=${cod_item}&is_total=${isTotal}`);
        const data = await response.json();
        return data.qtde_solic;
    } catch (error) {
        console.error("Erro ao obter quantidade solicitada na rota '/api/carga/qtde_solic?id_carga=<id_carga>&cod_item=<cod_item>':", error);
        return null;
    }
}


async function getPendingItems() {
    try {
        const response = await fetch('/get/itens_carga_incomp/' + nroCarga, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const result = await response.json();
        const items = result.items;

        // Fazer log no console e no servidor
        console.log('[DEBUG] itens pendentes:', items);
        console.log('[DEBUG] itens pendentes: ' + JSON.stringify(items));
        logOnServer('[DEBUG] itens pendentes: ' + JSON.stringify(items)); 

        const cod_items = items.map(item => item[1]);

        return cod_items;
    } catch (error) {
        console.error('Erro ao verificar se há itens pendentes na tabela carga_incomp:', error);
        
        return false;
    }
}


async function hasPendingItems() {
    const PendingItems = await getPendingItems();
    if (PendingItems.length > 0) { hasPendingItems = true } else { hasPendingItems = false };

    return hasPendingItems;
}


async function hasCargaAtHistory() {
    try {
        const response = await fetch('/get/has_carga_at_history/' + nroCarga, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const result = await response.json();
        const bool_result = result.bool;
        return bool_result;
    } catch (error) {
        console.error('Erro ao verificar se há cargas já faturadas neste código:', error);
        return false;
    }
}


async function concludeSeparacao() {
    // Obtém os dados da separação atual.
    // Seleciona o botão de finalizar separação.
    const sepCarga = await getSeparacao();
    const finalizarBtn = document.getElementById('finalizarBtn');

    // Exibe um indicador de carregamento e desativa o botão de finalizar.
    showLoading();
    finalizarBtn.onclick = '';
    finalizarBtn.innerHTML = '<span class="loader-inline"></span>';

    // Verifica se há uma carga no histórico.
    // Obtém os itens pendentes e verifica se há itens pendentes.
    const hasHistory = await hasCargaAtHistory();
    const PendingItems = await getPendingItems();
    const hasPendingItems = Array.isArray(PendingItems) && PendingItems.length > 0;
    
    // Inicializa a variável que armazenará os itens da carga.
    // Inicializa a variável que identifica se a separação é incompleta.
    let itensCarga = [];
    let isIncompSeparation = false;

    await visualDelay(200);

    if (!hasHistory) {
        // se não há carga no historico, continua a separação
        showToast('A carga é válida para ser separada...', 'success');
    } else {
        // se houver, verifica se a carga está completa antes de continuar
        if (!hasPendingItems) {
            // se não houver itens pendentes, aborta a separação
            showToast('A carga já está completa e finalizada.', 'error');
            return;
        } else {
            // se houver itens pendentes, prossegue a separação
            showToast('Continuando a separação da carga incompleta...', 'info');
            isIncompSeparation = true;
        }
    }

    await visualDelay(700);

    if (!hasPendingItems) {
        // Se não houver itens pendentes, tenta obter os itens da carga da API.
        try {
            const response = await fetch(`/api/itens_carga?id_carga=${nroCarga}`, {method: 'GET', headers: {'Content-Type': 'application/json'}});
            const result = await response.json();
            itensCarga = result.itens;
            console.log('[DEBUG] itens:', result.itens);
        } catch (error) {
            console.error('[ERROR] Erro ao obter itensCarga:', error);
            return;
        }
    } else {
        // Caso contrário, usa os itens pendentes obtidos anteriormente.
        itensCarga = PendingItems;
    }

    // Agrupa os itens separados pela carga atual com base no código do item.
    const groupedItems = sepCarga.reduce((acc, item) => {
        if (!acc[item.cod_item]) {
            acc[item.cod_item] = [];
        }
        acc[item.cod_item].push(item);
        return acc;
    }, {});
    
    var nonAvailableItems = [];

    // Para cada item na carga, verifica se a quantidade solicitada é igual à quantidade separada.
    for (const cod_item of itensCarga) {
        let subTotal = 0;

        if (groupedItems[cod_item]) {
            for (const item of groupedItems[cod_item]) {
                // Soma as quantidades separadas para este item
                subTotal += item.qtde_sep;
            }
        }
        // Recupera a quantidade solicitada para este item específico
        // ex.: fetchQtdeSolic(8967, '000123')
        const qtde_solic = await fetchQtdeSolic(nroCarga, cod_item);

        // Verifica se a quantidade solicitada é igual à quantidade separada
        if (qtde_solic > subTotal) {
            const qtde_faltante = qtde_solic - subTotal;
            // adiciona o item e quantidade
            // ao array de itens não disponíveis
            nonAvailableItems.push({ cod_item: cod_item, qtde_faltante: qtde_faltante });
            showToast(`Item ${cod_item}: ( ${subTotal} / ${qtde_solic} )`, 'warn');

        } else if (qtde_solic == subTotal) {
            showToast(`Item ${cod_item}: ( ${subTotal} / ${qtde_solic} )`, 'success');

        } else {
            showToast(`Item ${cod_item}: ( ${subTotal} / ${qtde_solic} )`, 'error');
            showToast(`Quantidade EXCEDENTE para o item ${cod_item}`, 'error');
            return;
        }
        await visualDelay(100);
    }

    let saveAsPendingItems;
    const confirmationText = `[CARGA: ${nroCarga}]\nVocê tem certeza que deseja finalizar a separação?\n`

    // Verifica se houve itens não separados
    if (nonAvailableItems.length > 0) {
        const itemsList = nonAvailableItems.map(item => `${item.cod_item}`).join(', ');
        const confirmation = confirm(
            `${confirmationText}\nALERTA:\nA quantidade total para os itens ${itemsList} não corresponde ao solicitado.`
        );
        if (confirmation) {
            saveAsPendingItems = true;
        } else {
            showToast('Operação cancelada.', 'error');
            hideLoading();
            await visualDelay(400);
            finalizarBtn.innerHTML = '✘';
            return;
        }
    }

    const confirmation = saveAsPendingItems || confirm(`${confirmationText}`);

    if (confirmation) {
        const storageKey = getStorageKey();
        const sepCarga = JSON.parse(localStorage.getItem(storageKey)) || [];
        
        if (sepCarga.length === 0) {
            
            showToast('Não há itens separados para finalizar.', 'error');
            return;
        }
    
        fetch('/logi/cargas/moving/bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(sepCarga),
        })
        .then(response => response.json())
        .then(async (data) => {
            if (data.success) {
                // se for uma separação incompleta, remove a pendencia da carga_incompleta
                if (isIncompSeparation) {
                    // Aguarda a conclusão da operação de remover pendências
                    try {
                        const concludeResponse = await fetch(`/api/conclude-incomp/${nroCarga}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                        });
                        
                        const concludeData = await concludeResponse.json();
        
                        if (concludeData.success) {
                            showToast('Pendência da carga removida com sucesso.', 'success', 10);
                        } else {
                            showToast(`<details><summary>Erro ao remover pendência da carga incompleta:</summary> ${concludeData.error}</details>`, 'error', 10);
                            return;
                        }
                    } catch (error) {
                        console.error('Erro ao remover pendência da carga incompleta:', error);
                        showToast(`<details><summary>Erro ao remover pendência da carga incompleta:</summary> ${error}</details>`, 'error', 10);
                        return; // Aborta o processo se houver erro
                    }
                }

                // cria a pendencia da carga_incompleta
                for (const item of nonAvailableItems) {
                    const { cod_item, qtde_faltante } = item;
                    console.log('[INFO] cod_item, qtde_faltante: ', cod_item, qtde_faltante);

                    try {
                        console.log('[INFO] Inserindo item na pendencia da carga_incompleta...');
                        const response = await fetch('/api/insert_carga_incomp', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                id_carga: nroCarga,
                                cod_item: cod_item,
                                qtde_atual: groupedItems[cod_item] ? groupedItems[cod_item].reduce((acc, item) => acc + item.qtde_sep, 0) : 0,
                                qtde_solic: qtde_faltante
                            })
                        });
                
                        const result = await response.json();
                        if (!result.success) {
                            // ERRO
                            console.error(`[ERROR] Erro ao inserir ${cod_item} para a carga incompleta.`, result.error);
                        } else {
                            // SUCESSO
                            console.log(`[INFO] Pendencias inseridas com sucesso para o item ${cod_item} (${qtde_faltante}).`);
                        }
                    } catch (error) {
                        // ERRO
                        console.error(`[ERROR] Erro ao enviar item ${cod_item} da carga incompleta para o database.`, error);
                    }
                }

                try {
                    getSeparacao().then(separacao => {
                        // envia json com separacao para o servidor
                        saveIntoServer(separacao, storageKey, 'cargas');
                    })
                    // limpa a separacao atual do cache (localStorage)
                    localStorage.removeItem(storageKey);
                } catch (error) {
                    // feedback visual para o front-end
                    // erro
                    showToast(`<details><summary>Erro ao finalizar separação:</summary> ${error}</details>`, 'error', 10);
                } finally {
                    // feedback visual para o front-end
                    // sucesso
                    hideLoading();
                    showToast('Separação da carga realizada com sucesso.', 'success', 10);
    
                    // gera relatório da separação
                    genCargaReport();
                }
            } else {
                showToast(`<details><summary>Erro ao finalizar separação:</summary> ${data.error}</details>`, 'error', 10);
            }
            // atualiza tabelas no front-end
            reloadTables();
            updateItemCount(0);
        })
        .catch(error => {
            console.error('Erro:', error);
            
            showToast(`<details><summary>Erro ao realizar movimentação em massa:</summary> ${error.message}</details>`, 'error', 10);
        });
    } else {
        showToast('Operação cancelada.', 'error');
        hideLoading();
        await visualDelay(400);
        finalizarBtn.innerHTML = '✘';
        return;
    }
}


const fetchItemDescription = async (cod_item) => {
    try {
        const response = await fetch(`/get/description_json/${cod_item}`);
        if (!response.ok) {
            throw new Error('Erro ao obter descrição do item');
        }
        const data = await response.json();
        // Retorna a descrição obtida
        return data.description;
    } catch (error) {
        console.error('Erro:', error);
        // Retorna uma string vazia
        return '';
    }
};


function sendCodItem(routePage, cod_item, carga_id, qtde_solic) {
    document.getElementById('cod_item_input').value = cod_item;
    document.getElementById('carga_id_input').value = carga_id;
    document.getElementById('qtde_item_input').value = qtde_solic;
    var form = document.getElementById('cod_item_form');
    form.action = `/logi/${routePage}/${carga_id}`;
    form.submit();
}

