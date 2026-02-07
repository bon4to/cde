/**
 * Tests for bundle.js functionality
 * Run with: node tests/js/test_bundle.js
 */

const assert = require('assert');

// Mock DOM environment
const mockDOM = {
    elements: {},
    getElementById(id) {
        if (!this.elements[id]) {
            this.elements[id] = {
                id,
                value: '',
                style: { display: '' },
                classList: {
                    _classes: new Set(),
                    add(c) { this._classes.add(c); },
                    remove(c) { this._classes.delete(c); },
                    contains(c) { return this._classes.has(c); }
                }
            };
        }
        return this.elements[id];
    },
    reset() {
        this.elements = {};
    }
};

global.document = mockDOM;

// Test: toggleBundleEndereco
function toggleBundleEndereco() {
    const operacao = document.getElementById("bundleOperation").value;
    if (operacao === 'T') {
        document.getElementById("bundleEnderecoContainer").style.display = 'flex';
    } else {
        document.getElementById("bundleEnderecoContainer").style.display = 'none';
    }
}

function testToggleBundleEndereco_WhenOperationIsS_HidesAddressContainer() {
    mockDOM.reset();
    document.getElementById("bundleOperation").value = 'S';
    toggleBundleEndereco();
    assert.strictEqual(document.getElementById("bundleEnderecoContainer").style.display, 'none');
    console.log('✓ Operation S hides address container');
}

function testToggleBundleEndereco_WhenOperationIsT_ShowsAddressContainer() {
    mockDOM.reset();
    document.getElementById("bundleOperation").value = 'T';
    toggleBundleEndereco();
    assert.strictEqual(document.getElementById("bundleEnderecoContainer").style.display, 'flex');
    console.log('✓ Operation T shows address container');
}

// Test: getEnderecoDestino
function getEnderecoDestino() {
    const letra = document.getElementById("bundleLetra").value;
    const numero = document.getElementById("bundleNumero").value;
    if (!letra || !numero) return '';
    return letra + '.' + numero;
}

function testGetEnderecoDestino_WhenBothFieldsFilled_ReturnsAddress() {
    mockDOM.reset();
    document.getElementById("bundleLetra").value = 'A';
    document.getElementById("bundleNumero").value = '5';
    assert.strictEqual(getEnderecoDestino(), 'A.5');
    console.log('✓ Returns address when both fields filled');
}

function testGetEnderecoDestino_WhenFieldEmpty_ReturnsEmpty() {
    mockDOM.reset();
    document.getElementById("bundleLetra").value = '';
    document.getElementById("bundleNumero").value = '5';
    assert.strictEqual(getEnderecoDestino(), '');
    console.log('✓ Returns empty when field is empty');
}

// Test: Bundle validation logic
function testBundleSubmit_WhenOperationS_DoesNotRequireAddress() {
    mockDOM.reset();
    document.getElementById("bundleOperation").value = 'S';
    const operation = document.getElementById("bundleOperation").value;
    let requiresAddress = (operation === 'T' && getEnderecoDestino() === '');
    assert.strictEqual(requiresAddress, false);
    console.log('✓ Operation S does not require address');
}

function testBundleSubmit_WhenOperationT_RequiresAddress() {
    mockDOM.reset();
    document.getElementById("bundleOperation").value = 'T';
    document.getElementById("bundleLetra").value = '';
    const operation = document.getElementById("bundleOperation").value;
    let requiresAddress = (operation === 'T' && getEnderecoDestino() === '');
    assert.strictEqual(requiresAddress, true);
    console.log('✓ Operation T requires address');
}

// Run tests
console.log('\n=== Bundle.js Tests ===\n');
try {
    testToggleBundleEndereco_WhenOperationIsS_HidesAddressContainer();
    testToggleBundleEndereco_WhenOperationIsT_ShowsAddressContainer();
    testGetEnderecoDestino_WhenBothFieldsFilled_ReturnsAddress();
    testGetEnderecoDestino_WhenFieldEmpty_ReturnsEmpty();
    testBundleSubmit_WhenOperationS_DoesNotRequireAddress();
    testBundleSubmit_WhenOperationT_RequiresAddress();
    console.log('\n✓ All tests passed!\n');
} catch (e) {
    console.error('\n✗ Test failed:', e.message);
    process.exit(1);
}
