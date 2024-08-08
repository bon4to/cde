// lb-cargas.js


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


function redirectToCarga(status) {
    const cargaInput = document.getElementById('cargaInput').value;
    if (cargaInput > 0) {
        const url = `/mov/separacao-${status}/${cargaInput}`;
        window.location.href = url;
    }
}


function listSeparationsLocalStorage() {
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
            window.location.href = `/mov/separacao-pend/${cargaNumber}`;
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

function generatePDF() {
    const { jsPDF } = window.jspdf;
    const report    = new jsPDF();

    const userName = document.getElementById('separador-info').innerText;
    const currentDateTime = new Date().toLocaleString();

    const tableData = [];
    const rows = document.querySelectorAll("#itemsTable tbody tr");

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

    const pageHeight   = report.internal.pageSize.height;
    const marginBottom = 20;
    const cellPadding  = 4;
    const cellHeight   = 10;
    const startX       = 10;
    const colWidths    = [25, 30, 80, 30, 25];
    let startY         = 50;

    const drawHeader = () => {
        report.setFont("times", "bold");
        report.setFontSize(16);
        report.text("Relatório de Cargas", 10, 22);

        report.setFont("times", "normal");
        report.setFontSize(12);
        report.text("INDUSTRIA DE SUCOS 4 LEGUA LTDA - EM RECUPERACAO JUDICIAL", 10, 28);

        if (typeof nroCarga !== 'undefined') {
            report.text(`CARGA: ${nroCarga}`, 10, 34);
        }

        if (typeof fantCliente !== 'undefined') {
            report.text(`CLIENTE: ${fantCliente}`, 10, 40);
        }

        report.setLineWidth(0.4);
        report.line(10, 44, 200, 44);
    };

    const drawFooter = () => {
        const totalPages = report.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            report.setPage(i);
            const pageNumber = report.internal.getCurrentPageInfo().pageNumber;

            report.setLineWidth(0.4);
            report.line(10, pageHeight - marginBottom, 200, pageHeight - marginBottom);

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
            report.rect(startX + colWidths.slice(0, i).reduce((a, b) => a + b, 0), startY, colWidths[i], cellHeight);
            report.text(col, startX + colWidths.slice(0, i).reduce((a, b) => a + b, 0) + cellPadding, startY + cellHeight / 2 + cellPadding / 2);
        });

        // Desenhando linhas da tabela
        startY += cellHeight;
        report.setFont("times", "normal");
        data.forEach((item, index) => {
            const row = [
                item.rua_letra_end,
                item.cod_item,
                item.desc_item,
                item.lote_item,
                item.qtde_solic.toString()
            ];

            const isSubtotal = item.lote_item && item.lote_item.startsWith('Subtotal:');
            const isTotal = item.lote_item === 'Total:';
            
            row.forEach((cell, i) => {
                if (isSubtotal) {
                    report.setFillColor(220, 220, 220);
                    report.setFont("times", "bold");
                } else if (isTotal) {
                    report.setFillColor(192, 192, 192);
                    report.setFont("times", "bold");
                } else {
                    report.setFillColor(255, 255, 255);
                    report.setFont("times", "normal");
                }

                const x = startX + colWidths.slice(0, i).reduce((a, b) => a + b, 0);
                const y = startY;

                report.rect(x, y, colWidths[i], cellHeight, 'F');

                const text = report.splitTextToSize(cell, colWidths[i] - 2 * cellPadding);
                report.text(text, x + cellPadding, y + cellPadding);
            });

            startY += cellHeight;

            // Verificar se há espaço suficiente na página
            if (startY + cellHeight + marginBottom > pageHeight) {
                report.addPage();
                drawHeader();
                startY = 50;
                report.setFontSize(10);
                report.setLineWidth(0.1);
            }
        });
    };

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


function listSeparationsFromServer() {
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
                        window.location.href = `/mov/separacao-done/${cargaNumber}`;
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


function sendToServer(data, filename) {
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





function bulkInsertHistorico() {
    const confirmation = confirm(`[CARGA: ${nroCarga}] Você tem certeza que deseja finalizar a separação?`);
    if (confirmation) {
        const storageKey = getStorageKey();
        const sepCarga = JSON.parse(localStorage.getItem(storageKey)) || [];
        
        if (sepCarga.length === 0) {
            alert('Não há dados para enviar.');
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
                alert('Movimentação em massa realizada com sucesso.');
                getSeparacao().then(separacao => {
                    sendToServer(separacao, storageKey) // envia json c/ dados do relatorio para o servidor
                })
                localStorage.removeItem(storageKey);    // limpa a separacao atual do localStorage
            } else {
                alert(`Erro ao realizar movimentação em massa:\n${data.error}`);
            }
            reloadTables();                             // atualiza tabelas no front-end
            updateItemCount(0);
        })
        .catch(error => {
            console.error('Erro:', error);
            alert(`Erro ao realizar movimentação em massa: ${error.message}`);
        });
    }
}


