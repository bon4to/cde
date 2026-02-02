/**
 * CDE Modal System
 *
 * Usage:
 *   // Simple modal
 *   Modal.open('myModal');
 *   Modal.close('myModal');
 *
 *   // Create modal programmatically
 *   Modal.create({
 *       id: 'confirmModal',
 *       title: 'Confirmar Ação',
 *       body: '<p>Deseja continuar?</p>',
 *       footer: [
 *           { text: 'Cancelar', class: 'modal-btn-secondary', action: 'close' },
 *           { text: 'Confirmar', class: 'modal-btn-primary', onclick: () => doSomething() }
 *       ]
 *   });
 */

const Modal = {
    /**
     * Open a modal by ID
     * @param {string} id - Modal ID (without #)
     */
    open(id) {
        const overlay = document.getElementById(id);
        if (overlay) {
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },

    /**
     * Close a modal by ID
     * @param {string} id - Modal ID (without #)
     */
    close(id) {
        const overlay = document.getElementById(id);
        if (overlay) {
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    },

    /**
     * Close all open modals
     */
    closeAll() {
        document.querySelectorAll('.modal-overlay.active').forEach(overlay => {
            overlay.classList.remove('active');
        });
        document.body.style.overflow = '';
    },

    /**
     * Create and append a modal to the DOM
     * @param {Object} options - Modal configuration
     * @param {string} options.id - Unique modal ID
     * @param {string} options.title - Modal title
     * @param {string} options.body - HTML content for modal body
     * @param {string} [options.size] - Modal size: 'sm', 'lg', 'xl' (default: normal)
     * @param {Array} [options.footer] - Footer buttons configuration
     * @param {boolean} [options.closeOnOverlay=true] - Close when clicking overlay
     * @returns {HTMLElement} The modal overlay element
     */
    create(options) {
        const { id, title, body, size, footer, closeOnOverlay = true } = options;

        // Remove existing modal with same ID
        const existing = document.getElementById(id);
        if (existing) existing.remove();

        // Build modal HTML
        const sizeClass = size ? `modal-${size}` : '';

        let footerHtml = '';
        if (footer && footer.length) {
            const buttons = footer.map(btn => {
                const btnClass = btn.class || 'modal-btn-secondary';
                const blockClass = btn.block ? 'modal-btn-block' : '';

                if (btn.action === 'close') {
                    return `<button class="modal-btn ${btnClass} ${blockClass}" onclick="Modal.close('${id}')">${btn.text}</button>`;
                }
                return `<button class="modal-btn ${btnClass} ${blockClass}" id="${id}_btn_${btn.text.toLowerCase().replace(/\s/g, '_')}">${btn.text}</button>`;
            }).join('');

            const footerClass = options.footerAlign ? `modal-footer-${options.footerAlign}` : '';
            const footerStack = options.footerStack ? 'modal-footer-stack' : '';
            footerHtml = `<div class="modal-footer ${footerClass} ${footerStack}">${buttons}</div>`;
        }

        const html = `
            <div id="${id}" class="modal-overlay">
                <div class="modal ${sizeClass}">
                    <div class="modal-header">
                        <h2>${title}</h2>
                        <button class="modal-close" onclick="Modal.close('${id}')">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${body}
                    </div>
                    ${footerHtml}
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', html);

        const overlay = document.getElementById(id);

        // Close on overlay click
        if (closeOnOverlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    Modal.close(id);
                }
            });
        }

        // Attach button onclick handlers
        if (footer) {
            footer.forEach(btn => {
                if (btn.onclick && btn.action !== 'close') {
                    const btnId = `${id}_btn_${btn.text.toLowerCase().replace(/\s/g, '_')}`;
                    const btnEl = document.getElementById(btnId);
                    if (btnEl) {
                        btnEl.addEventListener('click', btn.onclick);
                    }
                }
            });
        }

        return overlay;
    },

    /**
     * Quick confirm dialog
     * @param {string} message - Confirmation message
     * @param {Function} onConfirm - Callback when confirmed
     * @param {Object} [options] - Additional options
     */
    confirm(message, onConfirm, options = {}) {
        const id = 'modal_confirm_' + Date.now();

        Modal.create({
            id,
            title: options.title || 'Confirmar',
            body: `<p>${message}</p>`,
            footer: [
                { text: options.cancelText || 'Cancelar', class: 'modal-btn-secondary', action: 'close' },
                {
                    text: options.confirmText || 'Confirmar',
                    class: options.danger ? 'modal-btn-danger' : 'modal-btn-primary',
                    onclick: () => {
                        Modal.close(id);
                        if (onConfirm) onConfirm();
                    }
                }
            ],
            footerAlign: 'end'
        });

        Modal.open(id);
    },

    /**
     * Quick alert dialog
     * @param {string} message - Alert message
     * @param {Object} [options] - Additional options
     */
    alert(message, options = {}) {
        const id = 'modal_alert_' + Date.now();

        Modal.create({
            id,
            title: options.title || 'Aviso',
            body: `<p>${message}</p>`,
            footer: [
                { text: options.buttonText || 'OK', class: 'modal-btn-primary', action: 'close' }
            ],
            footerAlign: 'end'
        });

        Modal.open(id);
    },

    /**
     * Set modal body content
     * @param {string} id - Modal ID
     * @param {string} html - New body HTML
     */
    setBody(id, html) {
        const modal = document.getElementById(id);
        if (modal) {
            const body = modal.querySelector('.modal-body');
            if (body) body.innerHTML = html;
        }
    },

    /**
     * Get modal body element
     * @param {string} id - Modal ID
     * @returns {HTMLElement|null}
     */
    getBody(id) {
        const modal = document.getElementById(id);
        return modal ? modal.querySelector('.modal-body') : null;
    },

    /**
     * Set loading state on modal
     * @param {string} id - Modal ID
     * @param {boolean} loading - Loading state
     */
    setLoading(id, loading) {
        const modal = document.getElementById(id);
        if (!modal) return;

        const buttons = modal.querySelectorAll('.modal-btn');
        buttons.forEach(btn => {
            btn.disabled = loading;
            if (loading) {
                btn.dataset.originalText = btn.textContent;
                if (btn.classList.contains('modal-btn-primary')) {
                    btn.textContent = 'Carregando...';
                }
            } else if (btn.dataset.originalText) {
                btn.textContent = btn.dataset.originalText;
            }
        });
    }
};

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal-overlay.active');
        if (activeModal) {
            Modal.close(activeModal.id);
        }
    }
});
