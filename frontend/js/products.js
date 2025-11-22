/**
 * 商品管理功能
 */

let productsPage = 1;
let productsPageSize = 20;
let productsTotal = 0;

// 加载商品列表
async function loadProducts(page = 1) {
    productsPage = page;
    
    const name = document.getElementById('filterProductName').value;
    const model = document.getElementById('filterProductModel').value;
    const minPrice = document.getElementById('filterMinPrice').value.trim();
    const maxPrice = document.getElementById('filterMaxPrice').value.trim();
    
    const params = new URLSearchParams({
        page: page,
        page_size: productsPageSize,
    });
    
    if (name) params.append('name', name);
    if (model) params.append('model', model);
    // 验证价格输入是否为有效数字
    if (minPrice && !isNaN(parseFloat(minPrice)) && parseFloat(minPrice) >= 0) {
        params.append('min_price', parseFloat(minPrice));
    }
    if (maxPrice && !isNaN(parseFloat(maxPrice)) && parseFloat(maxPrice) >= 0) {
        params.append('max_price', parseFloat(maxPrice));
    }
    
    try {
        const response = await apiRequest(`/products/?${params}`);
        productsTotal = response.total;
        
        renderProductsTable(response.items);
        renderProductsPagination(response.page, response.page_size, response.total);
    } catch (error) {
        showMessage('加载商品列表失败: ' + error.message, 'error');
    }
}

// 渲染商品表格
function renderProductsTable(products) {
    const tbody = document.getElementById('productsTableBody');
    tbody.innerHTML = '';
    
    if (products.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }
    
    products.forEach(product => {
        const row = document.createElement('tr');
        
        const actions = `
            <div class="action-buttons">
                ${currentUser.user_type !== '厂家' ? `
                    <button class="action-btn btn-success" onclick="addToCart(${product.id})" title="添加到购物车">
                        <i class="fas fa-cart-plus"></i>
                    </button>
                ` : ''}
                <button class="action-btn" onclick="editProduct(${product.id})" title="修改">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn btn-danger" onclick="deleteProduct(${product.id})" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        const internalPrice = product.internal_price !== null && product.internal_price !== undefined
            ? formatCurrency(product.internal_price)
            : '-';
        
        row.innerHTML = `
            <td>${actions}</td>
            <td>${product.name}</td>
            <td>${product.model || '-'}</td>
            <td>${product.specification || '-'}</td>
            ${currentUser.user_type !== '厂家' ? `<td>${internalPrice}</td>` : ''}
            <td>${formatCurrency(product.tax_included_price)}</td>
            <td>${product.supplier_name || '-'}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// 渲染分页
function renderProductsPagination(page, pageSize, total) {
    const pagination = document.getElementById('productsPagination');
    const totalPages = Math.ceil(total / pageSize);
    
    pagination.innerHTML = `
        <button class="btn btn-secondary" ${page <= 1 ? 'disabled' : ''} onclick="loadProducts(${page - 1})">
            <i class="fas fa-chevron-left"></i> 上一页
        </button>
        <span class="pagination-info">第 ${page} 页，共 ${totalPages} 页，共 ${total} 条</span>
        <button class="btn btn-secondary" ${page >= totalPages ? 'disabled' : ''} onclick="loadProducts(${page + 1})">
            下一页 <i class="fas fa-chevron-right"></i>
        </button>
    `;
}

// 打开商品编辑/新建模态框
async function openProductModal(productId = null) {
    let product = null;
    let suppliers = [];
    
    // 如果是编辑模式，加载商品数据
    if (productId) {
        try {
            product = await apiRequest(`/products/${productId}`);
        } catch (error) {
            showMessage('加载商品信息失败: ' + error.message, 'error');
            return;
        }
    }
    
    // 加载厂家列表（用于下拉选择）
    try {
        const suppliersResponse = await apiRequest('/api/suppliers/');
        suppliers = suppliersResponse;
    } catch (error) {
        // 如果获取厂家列表失败，尝试从商品数据中获取
        if (product && product.supplier_id) {
            suppliers = [{ id: product.supplier_id, name: product.supplier_name }];
        }
    }
    
    // 构建表单HTML
    const canViewInternal = currentUser.user_type !== '厂家';
    const isSupplier = currentUser.user_type === '厂家';
    
    let formHtml = `
        <form id="productForm">
            <div class="form-group">
                <label><i class="fas fa-tag"></i> 商品名 *</label>
                <input type="text" name="name" value="${product ? product.name : ''}" required maxlength="200">
            </div>
            <div class="form-group">
                <label><i class="fas fa-cog"></i> 型号</label>
                <input type="text" name="model" value="${product ? (product.model || '') : ''}" maxlength="100">
            </div>
            <div class="form-group">
                <label><i class="fas fa-info-circle"></i> 规格</label>
                <textarea name="specification" maxlength="500">${product ? (product.specification || '') : ''}</textarea>
            </div>
    `;
    
    if (!isSupplier || !productId) {
        // 新建商品时，厂家用户需要选择厂家；编辑时显示厂家信息
        if (isSupplier) {
            formHtml += `
                <div class="form-group">
                    <label><i class="fas fa-building"></i> 厂家</label>
                    <input type="hidden" name="supplier_id" value="${currentUser.id}">
                    <input type="text" value="${currentUser.username}" disabled style="background: var(--color-surface-muted);">
                </div>
            `;
        } else {
            formHtml += `
                <div class="form-group">
                    <label><i class="fas fa-building"></i> 厂家 *</label>
                    <select name="supplier_id" required ${productId ? 'disabled style="background: var(--color-surface-muted);"' : ''}>
                        <option value="">请选择厂家</option>
                        ${suppliers.map(s => `
                            <option value="${s.id}" ${product && product.supplier_id === s.id ? 'selected' : ''}>
                                ${s.name}
                            </option>
                        `).join('')}
                    </select>
                </div>
            `;
        }
    } else {
        formHtml += `<input type="hidden" name="supplier_id" value="${product.supplier_id}">`;
    }
    
    if (canViewInternal) {
        formHtml += `
            <div class="form-group">
                <label><i class="fas fa-dollar-sign"></i> 内部价格 *</label>
                <input type="text" name="internal_price" value="${product ? (product.internal_price || '') : ''}" 
                       placeholder="请输入内部价格" required>
            </div>
        `;
    }
    
    formHtml += `
            <div class="form-group">
                <label><i class="fas fa-money-bill"></i> 含税价格 *</label>
                <input type="text" name="tax_included_price" value="${product ? product.tax_included_price : ''}" 
                       placeholder="请输入含税价格" required>
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal('productModal')">取消</button>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save"></i> 保存
                </button>
            </div>
        </form>
    `;
    
    const modal = createModal('productModal', productId ? '编辑商品' : '新建商品', formHtml);
    document.getElementById('modalContainer').appendChild(modal);
    openModal('productModal');
    
    // 绑定表单提交事件
    document.getElementById('productForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveProduct(productId);
    });
}

// 保存商品
async function saveProduct(productId) {
    const form = document.getElementById('productForm');
    const formData = getFormData(form);
    
    // 验证含税价格输入
    const taxIncludedPrice = parseFloat(formData.tax_included_price);
    if (isNaN(taxIncludedPrice) || taxIncludedPrice < 0) {
        showMessage('含税价格必须是有效的正数', 'error');
        return;
    }
    
    const data = {
        name: formData.name,
        model: formData.model || null,
        specification: formData.specification || null,
        tax_included_price: taxIncludedPrice,
        supplier_id: parseInt(formData.supplier_id),
    };
    
    // 厂家用户新建商品时，内部价格默认为含税价格
    if (currentUser.user_type === '厂家') {
        if (!productId) {
            data.internal_price = data.tax_included_price;
        }
    } else {
        // 验证内部价格输入
        const internalPrice = parseFloat(formData.internal_price);
        if (isNaN(internalPrice) || internalPrice < 0) {
            showMessage('内部价格必须是有效的正数', 'error');
            return;
        }
        data.internal_price = internalPrice;
    }
    
    try {
        if (productId) {
            // 更新商品
            await apiRequest(`/products/${productId}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showMessage('商品更新成功', 'success');
        } else {
            // 创建商品
            await apiRequest('/products/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showMessage('商品创建成功', 'success');
        }
        
        closeModal('productModal');
        loadProducts(productsPage);
    } catch (error) {
        showMessage((productId ? '更新' : '创建') + '商品失败: ' + error.message, 'error');
    }
}

// 编辑商品
function editProduct(productId) {
    openProductModal(productId);
}

// 删除商品
async function deleteProduct(productId) {
    if (!await confirmDialog('确定要删除这个商品吗？')) {
        return;
    }
    
    try {
        await apiRequest(`/products/${productId}`, { method: 'DELETE' });
        showMessage('商品删除成功', 'success');
        loadProducts(productsPage);
    } catch (error) {
        showMessage('删除商品失败: ' + error.message, 'error');
    }
}

// 添加到购物车
function addToCart(productId) {
    // 购物车功能在cart.js中实现
    if (typeof addProductToCart === 'function') {
        addProductToCart(productId);
    }
}

