// lb-cargas.js

let headerMainLogo;

var itemCount = 0;

if (nroCarga != '') {
    renderCartSubtotals();
}


function getStorageKey() {
    return `separacao-carga-${nroCarga}`;
}


function updateItemCount(itemCount) {
    document.querySelector('.item-count').textContent = itemCount;
}


function redirectToCarga(route) {
    const cargaInput = document.getElementById('cargaInput').value;
    if (cargaInput > 0) {
        const url = `/mov/${route}/${cargaInput}`;
        window.location.href = url;
    }
}


function listSeparationsLocalStorage(route) {
    const allSeparationsTable = document.getElementById('allSeparationsTable').getElementsByTagName('tbody')[0];
    allSeparationsTable.innerHTML = '';
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('separacao-carga-')) {
            keys.push(key);
        }
    }

    keys.sort((a, b) => b.localeCompare(a));

    keys.forEach(key => {
        const cargaNumber = key.replace('separacao-carga-', '');
        const row = allSeparationsTable.insertRow();
        row.insertCell(0).textContent = cargaNumber;
        row.classList.add("selectable-row");

        row.addEventListener('click', function() {
            window.location.href = `/mov/${route}/${cargaNumber}`;
        });
    });
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


function genCargaReport() {
    const { jsPDF } = window.jspdf;
    const report    = new jsPDF();
    const tableData = [];
    const rows      = document.querySelectorAll("#itemsTable tbody tr");
    const userName  = document.getElementById('separador-info').innerText;

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
        report.text("Relatório de Cargas", 10, 22);

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

        const pdfName = `${getStorageKey()}.pdf`;
        report.save(pdfName);
    });
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
        console.error('Erro ao obter separação:', error);
    });
}


function listSeparationsFromServer(route) {
    fetch('/get/list-all-separations')
        .then(response => response.json())
        .then(files => {
            const tableBody = document.getElementById('allSeparationsTable').getElementsByTagName('tbody')[0];
            tableBody.innerHTML = '';

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

                    row.addEventListener('click', function() {
                        window.location.href = `/mov/${route}/${cargaNumber}`;
                    });
                });
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
                <span class="item-quantity cor-web">${subtotal}</span>
            `;
            cartItemsContainer.appendChild(listItem);
            itemCount += 1;

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
        });
        
        updateItemCount(itemCount);
    }).catch(error => {
        console.error('Erro ao obter separação:', error);
        
    });
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


function saveIntoServer(data, filename) {
    const payload = {
        data: data,
        filename: filename
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


function pushItemIntoSeparacao(maxEstoque, qtdeSolic, rua_letra, rua_numero, lote_item) {
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

    input.value = 0

    msge.textContent = `${qtde_separada} / ${qtde_solic}`;
    obsv.textContent = `${maxEstoque} em estoque (${this_qtde_separada} utilizado)`;
    info.textContent = `(${qtde_faltante} faltante)`;

    maxEstoque = maxEstoque - this_qtde_separada
    input.max = Math.min(qtde_faltante, maxEstoque);

    maxBtn.onclick = function() {
        input.value = input.max;
    };
    
    if (qtde_faltante <= 0) {
        alert(`O item ${codItem} já possui quantidade suficiente.\nRemova suas separações, caso precise substituir.`)
    } else {
        popup.classList.remove('hidden');

        submitBtn.onclick = function() {
            const value = parseInt(input.value);
            if (value > 0 && value <= input.max) {
                popup.classList.add('hidden');
                onSubmit(value);
                renderCartSubtotals();
            } else {
                alert(`Por favor, insira uma quantidade válida (entre 1 e ${input.max}).`);
            }
        };
    }
}


function hidePopUp() {
    const popup = document.getElementById('quantityPopup');
    popup.classList.add('hidden');
}


async function fetchQtdeSolic(id_carga, cod_item) {
    try {
        const response = await fetch(`/api/qtde_solic?id_carga=${id_carga}&cod_item=${cod_item}`);
        const data = await response.json();
        return data.qtde_solic;
    } catch (error) {
        console.error('Erro ao obter qtde_solic:', error);
        return null;
    }
}


async function concludeSeparacao() {
    const sepCarga = await getSeparacao();
    const finalizarBtn = document.getElementById('finalizarBtn');

    // checar se ha itens pendentes, se houver, abortar o processamento 
    // (caso esta carga exista no historico)
    await checkPendingItems(); 

    finalizarBtn.onclick = '';
    finalizarBtn.innerHTML = '<span class="loader-inline"></span>';

    let itens_carga = [];

    try {
        const response = await fetch('/api/itens_carga?id_carga=' + nroCarga, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const result = await response.json();
        itens_carga = result.itens;
        console.log('itens_carga:', itens_carga);
    } catch (error) {
        console.error('Erro ao obter itens_carga:', error);
        return;
    }

    const groupedItems = sepCarga.reduce((acc, item) => {
        if (!acc[item.cod_item]) {
            acc[item.cod_item] = [];
        }
        acc[item.cod_item].push(item);
        return acc;
    }, {});
    
    var nonAvailableItems = [];

    for (const cod_item of itens_carga) {
        let subtotal = 0;

        if (groupedItems[cod_item]) {
            for (const item of groupedItems[cod_item]) {
                subtotal += item.qtde_sep;  // Soma as quantidades separadas para este item
            }
        }

        const qtde_solic = await fetchQtdeSolic(nroCarga, cod_item);  // Recupera a quantidade solicitada para este item específico

        if (qtde_solic !== subtotal) {  // Verifica se a quantidade solicitada é igual à quantidade separada
            console.error('Item:', cod_item, 'qtde_solic:', qtde_solic, 'subtotal:', subtotal);
            alert(`ALERTA:\n${cod_item} | ${subtotal} / ${qtde_solic}\n(quantidade insuficiente)`);
            nonAvailableItems.push(cod_item);
        } else {
            console.log('Item:', cod_item, 'qtde_solic:', qtde_solic, 'subtotal:', subtotal);
        }
    }
    
    let hasPendingItems;

    if (nonAvailableItems.length > 0) {
        const confirmation = confirm(
            `[CARGA: ${nroCarga}]\nVocê tem certeza que deseja finalizar a separação?\nALERTA:\nA quantidade total para os itens ${nonAvailableItems.join(', ')} não corresponde ao solicitado.`
        );
        if (confirmation) {
            hasPendingItems = true;
            
            for (const cod_item of nonAvailableItems) {
                // Verifica se groupedItems[cod_item] está definido
                let subtotal = 0;
                if (groupedItems[cod_item]) {
                    subtotal = groupedItems[cod_item].reduce((acc, item) => acc + item.qtde_sep, 0);
                }
    
                const qtde_solic = await fetchQtdeSolic(nroCarga, cod_item);
                
                try {
                    // Enviar dados para o servidor
                    const response = await fetch('/api/insert_carga_pendente', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            id_carga: nroCarga,
                            cod_item: cod_item,
                            qtde_atual: subtotal,
                            qtde_solic: qtde_solic
                        })
                    });
                    
                    const result = await response.json();
                    if (!result.success) {
                        console.error(`Erro ao inserir ${cod_item} como pendente para a carga.`, result.error);
                    }
                } catch (error) {
                    console.error(`Erro ao enviar carga pendente para o servidor para o item ${cod_item}:`, error);
                }
            }
        } else {
            reloadPage();
            return;
        }
    }

    let confirmation;

    if (!hasPendingItems) {
        confirmation = confirm(`[CARGA: ${nroCarga}]\nVocê tem certeza que deseja finalizar a separação?`);
    } else {
        confirmation = true;
    }

    if (confirmation) {
        const storageKey = getStorageKey();
        const sepCarga = JSON.parse(localStorage.getItem(storageKey)) || [];
        
        if (sepCarga.length === 0) {
            alert('ALERTA:\nNão há itens separados para finalizar.\nA operação foi cancelada.');
            reloadPage();
            return;
        }
    
        fetch('/mov/moving/bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(sepCarga),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('INFO:\nSeparação da carga realizada com sucesso.');
                getSeparacao().then(separacao => {
                    saveIntoServer(separacao, storageKey) // envia json c/ dados do relatorio para o servidor
                })
                localStorage.removeItem(storageKey);      // limpa a separacao atual do localStorage
            } else {
                alert(`Erro ao realizar movimentação em massa:\n${data.error}`);
            }
            reloadTables();                               // atualiza tabelas no front-end
            updateItemCount(0);
        })
        .catch(error => {
            console.error('Erro:', error);
            alert(`Erro ao realizar movimentação em massa: ${error.message}`);
        });
    }
}


const fetchItemDescription = async (cod_item) => {
    try {
        const response = await fetch(`/get/description_json/${cod_item}`);
        if (!response.ok) {
            throw new Error('Erro ao obter descrição do item');
        }
        const data = await response.json();
        return data.description; // Retorna a descrição obtida
    } catch (error) {
        console.error('Erro:', error);
        return ''; // Retorna uma string vazia ou outro valor de erro
    }
};


function sendCodItem(route, cod_item, carga_id, qtde_solic) {
    document.getElementById('cod_item_input').value = cod_item;
    document.getElementById('carga_id_input').value = carga_id;
    document.getElementById('qtde_item_input').value = qtde_solic;
    var form = document.getElementById('cod_item_form');
    form.action = `/mov/${route}/${carga_id}`;
    form.submit();
}

