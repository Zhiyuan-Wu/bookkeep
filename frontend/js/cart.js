/**
 * 购物车功能
 */

let cart = {}; // { supplierId: { supplierName: string, items: [] } }

// 添加到购物车
async function addProductToCart(productId) {
    try {
        const product = await apiRequest(`/products/${productId}`);
        
        const supplierId = product.supplier_id;
        if (!cart[supplierId]) {
            cart[supplierId] = {
                supplierName: product.supplier_name || '未知厂家',
                items: []
            };
        }
        
        // 检查是否已存在
        const existingItem = cart[supplierId].items.find(item => item.product_id === productId);
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart[supplierId].items.push({
                product_id: product.id,
                name: product.name,
                brand: product.brand || '',
                model: product.model || '',
                specification: product.specification || '',
                internal_price: product.internal_price,
                tax_included_price: product.tax_included_price,
                quantity: 1,
                muted: false
            });
        }
        
        updateCartBadge();
        showMessage('已添加到购物车', 'success');
    } catch (error) {
        showMessage('添加到购物车失败: ' + error.message, 'error');
    }
}

// 更新购物车徽章
function updateCartBadge() {
    const cartBtn = document.getElementById('cartBtn');
    if (!cartBtn) return;
    
    let totalItems = 0;
    
    // 计算所有商品的总数量（不是商品种类数）
    for (const supplierId in cart) {
        cart[supplierId].items.forEach(item => {
            totalItems += item.quantity;
        });
    }
    
    // 移除旧徽章
    const oldBadge = cartBtn.querySelector('.cart-badge');
    if (oldBadge) {
        oldBadge.remove();
    }
    
    // 添加新徽章
    if (totalItems > 0) {
        const badge = document.createElement('span');
        badge.className = 'cart-badge';
        badge.textContent = totalItems;
        cartBtn.appendChild(badge);
    }
}

// 打开购物车模态框
window.openCartModal = function openCartModal() {
    // 如果模态框已存在，先移除
    const existingModal = document.getElementById('cartModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = createModal('cartModal', '购物车', renderCartContent());
    document.getElementById('modalContainer').appendChild(modal);
    openModal('cartModal');
}

// 渲染购物车内容
function renderCartContent() {
    // 检测是否为移动端
    const isMobile = window.innerWidth <= 768;

    if (Object.keys(cart).length === 0) {
        return '<div class="cart-empty"><i class="fas fa-shopping-cart"></i><p>购物车为空</p></div>';
    }

    let html = '<div class="cart-items">';

    for (const supplierId in cart) {
        const group = cart[supplierId];

        if (isMobile) {
            // 移动端：卡片式布局
            html += `
                <div class="cart-group">
                    <div class="cart-group-header">
                        <i class="fas fa-building"></i>
                        <h3>${group.supplierName}</h3>
                    </div>
                    <div class="cart-items-mobile">
            `;

            group.items.forEach((item, index) => {
                const mutedClass = item.muted ? 'muted' : '';
                html += `
                    <div class="cart-item-card ${mutedClass}" data-supplier-id="${supplierId}" data-index="${index}">
                        <div class="cart-item-header">
                            <span class="cart-item-name">${item.name}</span>
                            <div style="display: flex; gap: 8px;">
                                <button class="action-btn" onclick="window.toggleMute(${supplierId}, ${index})" title="${item.muted ? '显示' : '隐藏'}">
                                    <i class="fas fa-eye${item.muted ? '-slash' : ''}"></i>
                                </button>
                                <button class="action-btn btn-danger" onclick="window.removeFromCart(${supplierId}, ${index})" title="删除">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        <div class="cart-item-details">
                            ${item.brand ? `<span class="cart-item-detail"><i class="fas fa-tag"></i>${item.brand}</span>` : ''}
                            ${item.model ? `<span class="cart-item-detail"><i class="fas fa-cog"></i>${item.model}</span>` : ''}
                        </div>
                        <div class="cart-item-price">
                            ${(currentUser.user_type !== '厂家' && currentUser.user_type !== '学生用户' && item.internal_price !== null && item.internal_price !== undefined) ?
                                `<span class="price-internal">内部: ${formatCurrency(item.internal_price)}</span>` : ''}
                            <span class="price-tax">含税: ${formatCurrency(item.tax_included_price)}</span>
                        </div>
                        <div class="cart-item-quantity">
                            <button class="qty-btn" onclick="window.adjustQuantity(${supplierId}, ${index}, -1)">-</button>
                            <input type="number" value="${item.quantity}" class="qty-input"
                                   data-supplier-id="${supplierId}"
                                   data-item-index="${index}"
                                   onchange="window.updateCartQuantityFromInput(this, ${supplierId}, ${index})">
                            <button class="qty-btn" onclick="window.adjustQuantity(${supplierId}, ${index}, 1)">+</button>
                        </div>
                    </div>
                `;
            });

            html += '</div></div>';
        } else {
            // PC端：保持原有表格布局
            html += `
                <div class="cart-group">
                    <div class="cart-group-header">
                        <i class="fas fa-building"></i>
                        <h3>${group.supplierName}</h3>
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th style="width: 7%;">操作</th>
                                <th style="width: 7%;">隐藏</th>
                                <th style="width: 18%;">商品名</th>
                                <th style="width: 10%;">品牌</th>
                                <th style="width: 10%;">型号</th>
                                <th style="width: 15%;">规格</th>
                                ${currentUser.user_type !== '厂家' && currentUser.user_type !== '学生用户' ? '<th style="width: 11%;">内部价格</th>' : ''}
                                <th style="width: 11%;">含税价格</th>
                                <th style="width: 11%;">数量</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            group.items.forEach((item, index) => {
                const mutedClass = item.muted ? 'muted' : '';
                html += `
                    <tr class="${mutedClass}">
                        <td>
                            <button class="action-btn btn-danger" onclick="window.removeFromCart(${supplierId}, ${index})" title="删除">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                        <td>
                            <button class="action-btn" onclick="window.toggleMute(${supplierId}, ${index})" title="${item.muted ? '显示' : '隐藏'}">
                                <i class="fas fa-eye${item.muted ? '-slash' : ''}"></i>
                            </button>
                        </td>
                        <td>${item.name}</td>
                        <td>${item.brand || '-'}</td>
                        <td>${item.model || '-'}</td>
                        <td>${item.specification || '-'}</td>
                        ${(currentUser.user_type !== '厂家' && currentUser.user_type !== '学生用户') ? `<td>${item.internal_price !== null && item.internal_price !== undefined ? formatCurrency(item.internal_price) : '-'}</td>` : ''}
                        <td>${formatCurrency(item.tax_included_price)}</td>
                        <td>
                            <input type="text" value="${item.quantity}"
                                   data-supplier-id="${supplierId}"
                                   data-item-index="${index}"
                                   class="cart-quantity-input"
                                   style="width: 60px; padding: 8px 10px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface-muted); font-size: 0.95rem; transition: var(--transition-base);"
                                   onfocus="this.style.background='var(--color-surface)'; this.style.borderColor='var(--color-primary)'; this.style.boxShadow='0 0 0 3px rgba(20, 118, 255, 0.12)'"
                                   onblur="this.style.background='var(--color-surface-muted)'; this.style.borderColor='var(--color-border)'; this.style.boxShadow='none'; window.updateCartQuantity(this)">
                        </td>
                    </tr>
                `;
            });

            html += '</tbody></table></div>';
        }
    }

    // 计算总计
    let totalInternal = 0;
    let totalTaxIncluded = 0;

    for (const supplierId in cart) {
        cart[supplierId].items.forEach(item => {
            if (!item.muted) {
                // 计算内部价格（非厂家用户且内部价格不为null/undefined）
                if (currentUser.user_type !== '厂家' && currentUser.user_type !== '学生用户' && item.internal_price !== null && item.internal_price !== undefined) {
                    totalInternal += (item.internal_price || 0) * item.quantity;
                }
                // 计算含税价格
                totalTaxIncluded += (item.tax_included_price || 0) * item.quantity;
            }
        });
    }

    // 构建总计文本
    let totalText = '总计：';
    if (currentUser.user_type !== '厂家' && currentUser.user_type !== '学生用户') {
        totalText += `内部${formatCurrency(totalInternal)}/含税${formatCurrency(totalTaxIncluded)}`;
    } else {
        totalText += `含税${formatCurrency(totalTaxIncluded)}`;
    }

    html += `
        <div class="cart-total-row" id="cartTotalRow">
            <div class="cart-total-text" id="cartTotalText">${totalText}</div>
        </div>
        <div class="form-actions" style="margin-top: 20px; justify-content: flex-end;">
            <button class="btn btn-primary" onclick="window.saveOrder()">
                <i class="fas fa-save"></i> 保存订单
            </button>
        </div>
    `;

    return html;
}

// 从购物车移除商品
window.removeFromCart = function removeFromCart(supplierId, index) {
    cart[supplierId].items.splice(index, 1);
    if (cart[supplierId].items.length === 0) {
        delete cart[supplierId];
    }
    updateCartBadge();
    refreshCartModal();
}

// 切换静音状态
window.toggleMute = function toggleMute(supplierId, index) {
    cart[supplierId].items[index].muted = !cart[supplierId].items[index].muted;
    refreshCartModal();
}

// 更新数量（从输入框）
window.updateCartQuantity = function updateCartQuantity(input) {
    const supplierId = parseInt(input.dataset.supplierId);
    const index = parseInt(input.dataset.itemIndex);
    const quantity = parseInt(input.value);
    
    if (isNaN(quantity) || quantity < 1) {
        showMessage('数量必须是大于0的整数', 'error');
        // 恢复原值
        const originalQty = cart[supplierId].items[index].quantity;
        input.value = originalQty;
        return;
    }
    
    cart[supplierId].items[index].quantity = quantity;
    updateCartBadge();
    updateCartTotals();
}

// 更新购物车总计（不重新渲染整个模态框）
function updateCartTotals() {
    let totalInternal = 0;
    let totalTaxIncluded = 0;
    
    for (const supplierId in cart) {
        cart[supplierId].items.forEach(item => {
            if (!item.muted) {
                // 计算内部价格（非厂家用户且内部价格不为null/undefined）
                if (currentUser.user_type !== '厂家' && currentUser.user_type !== '学生用户' && item.internal_price !== null && item.internal_price !== undefined) {
                    totalInternal += (item.internal_price || 0) * item.quantity;
                }
                // 计算含税价格
                totalTaxIncluded += (item.tax_included_price || 0) * item.quantity;
            }
        });
    }
    
    // 更新总计显示
    const totalTextEl = document.getElementById('cartTotalText');
    if (totalTextEl) {
        let totalText = '总计：';
        if (currentUser.user_type !== '厂家') {
            totalText += `内部${formatCurrency(totalInternal)}/含税${formatCurrency(totalTaxIncluded)}`;
        } else {
            totalText += `含税${formatCurrency(totalTaxIncluded)}`;
        }
        totalTextEl.textContent = totalText;
    }
}

// 刷新购物车模态框内容（不关闭模态框）
function refreshCartModal() {
    const modal = document.getElementById('cartModal');
    if (!modal) return;
    
    const modalBody = modal.querySelector('.modal-body');
    if (modalBody) {
        modalBody.innerHTML = renderCartContent();
    }
    updateCartBadge();
}

// 保存订单
window.saveOrder = async function saveOrder() {
    if (Object.keys(cart).length === 0) {
        showMessage('购物车为空', 'warning');
        return;
    }
    
    try {
        // 为每个厂家创建一个订单
        for (const supplierId in cart) {
            const group = cart[supplierId];
            const items = group.items.map(item => ({
                product_id: item.product_id,
                name: item.name,
                brand: item.brand,
                model: item.model,
                specification: item.specification,
                internal_price: item.internal_price,
                tax_included_price: item.tax_included_price,
                quantity: item.quantity,
                muted: item.muted
            }));
            
            await apiRequest('/orders/', {
                method: 'POST',
                body: JSON.stringify({
                    supplier_id: parseInt(supplierId),
                    items: items
                })
            });
        }
        
        // 清空购物车
        cart = {};
        updateCartBadge();
        closeModal('cartModal');
        showMessage('订单保存成功', 'success');
        
        // 刷新订单列表
        if (currentPage === 'orders') {
            loadOrders();
        }
    } catch (error) {
        showMessage('保存订单失败: ' + error.message, 'error');
    }
}

// 创建模态框
function createModal(id, title, content) {
    const modal = document.createElement('div');
    modal.id = id;
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>${title}</h3>
                <button class="modal-close" onclick="closeModal('${id}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
        </div>
    `;
    
    // 点击背景关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal(id);
        }
    });
    
    return modal;
}

// ==================== 移动端购物车辅助函数 ====================

// 调整数量（移动端+/-按钮）
window.adjustQuantity = function adjustQuantity(supplierId, index, delta) {
    const item = cart[supplierId].items[index];
    const newQuantity = item.quantity + delta;

    if (newQuantity < 1) {
        showMessage('数量不能小于1', 'error');
        return;
    }

    item.quantity = newQuantity;
    updateCartBadge();
    updateCartTotals();

    // 更新输入框显示
    const input = document.querySelector(`.qty-input[data-supplier-id="${supplierId}"][data-item-index="${index}"]`);
    if (input) {
        input.value = newQuantity;
    }
};

// 从输入框更新数量（移动端）
window.updateCartQuantityFromInput = function updateCartQuantityFromInput(input, supplierId, index) {
    const quantity = parseInt(input.value);

    if (isNaN(quantity) || quantity < 1) {
        showMessage('数量必须是大于0的整数', 'error');
        // 恢复原值
        input.value = cart[supplierId].items[index].quantity;
        return;
    }

    cart[supplierId].items[index].quantity = quantity;
    updateCartBadge();
    updateCartTotals();
};

