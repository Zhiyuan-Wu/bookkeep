/**
 * 统计信息功能
 */

// 存储统计信息数据，用于窗口大小改变时重新渲染
let statisticsData = null;

// 加载统计信息
async function loadStatistics() {
    try {
        const response = await apiRequest('/statistics/');
        statisticsData = { items: response.items, total: response.total };
        renderStatisticsTable(statisticsData.items, statisticsData.total);
    } catch (error) {
        showMessage('加载统计信息失败: ' + error.message, 'error');
    }
}

// 监听窗口大小改变，重新渲染统计信息
window.addEventListener('resize', () => {
    // 如果当前在统计信息页面且有数据，则重新渲染
    if (currentPage === 'statistics' && statisticsData) {
        renderStatisticsTable(statisticsData.items, statisticsData.total);
    }
});

// 渲染统计表格
function renderStatisticsTable(items, total) {
    // 检测是否为移动端
    const isMobile = window.innerWidth <= 768;

    // 查找或创建移动端容器
    let mobileContainer = document.getElementById('statisticsMobileContainer');
    const table = document.querySelector('.stats-table');

    if (isMobile) {
        // 移动端：隐藏表格，显示卡片
        if (table) {
            table.style.display = 'none';
        }

        // 创建移动端容器
        if (!mobileContainer) {
            mobileContainer = document.createElement('div');
            mobileContainer.id = 'statisticsMobileContainer';
            mobileContainer.className = 'cart-items-mobile';
            // 插入到表格后面
            if (table && table.parentNode) {
                table.parentNode.insertBefore(mobileContainer, table.nextSibling);
            }
        }

        let html = '';

        if (items.length === 0) {
            html = '<div class="cart-item-card"><p style="text-align: center; padding: 40px; color: var(--color-muted);">暂无数据</p></div>';
        } else {
            // 渲染各供应商数据
            items.forEach(item => {
                html += `
                    <div class="cart-item-card">
                        <div class="cart-item-header">
                            <span class="cart-item-name">${item.supplier_name}</span>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px;">
                            <div class="stat-row">
                                <span class="stat-label">订单总数</span>
                                <span class="stat-value">${item.order_count}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">商品总数</span>
                                <span class="stat-value">${item.product_count}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">订单总内部价格</span>
                                <span class="stat-value">${formatCurrency(item.total_internal_price)}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">订单总含税价格</span>
                                <span class="stat-value">${formatCurrency(item.total_tax_included_price)}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">总服务价格</span>
                                <span class="stat-value">${formatCurrency(item.total_service_amount)}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">总税额</span>
                                <span class="stat-value">${formatCurrency(item.total_tax)}</span>
                            </div>
                            <div class="stat-row" style="border-top: 2px solid var(--color-primary); padding-top: 8px; margin-top: 4px;">
                                <span class="stat-label" style="color: var(--color-primary); font-weight: 600;">总结余</span>
                                <span class="stat-value" style="color: var(--color-primary); font-weight: 600;">${formatCurrency(item.total_balance)}</span>
                            </div>
                        </div>
                    </div>
                `;
            });

            // 渲染总计卡片
            html += `
                <div class="cart-item-card" style="background: rgba(20, 118, 255, 0.08); border-color: var(--color-primary);">
                    <div class="cart-item-header">
                        <span class="cart-item-name" style="color: var(--color-primary);">${total.supplier_name}</span>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px;">
                        <div class="stat-row">
                            <span class="stat-label">订单总数</span>
                            <span class="stat-value"><strong>${total.order_count}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">商品总数</span>
                            <span class="stat-value"><strong>${total.product_count}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">订单总内部价格</span>
                            <span class="stat-value"><strong>${formatCurrency(total.total_internal_price)}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">订单总含税价格</span>
                            <span class="stat-value"><strong>${formatCurrency(total.total_tax_included_price)}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">总服务价格</span>
                            <span class="stat-value"><strong>${formatCurrency(total.total_service_amount)}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">总税额</span>
                            <span class="stat-value"><strong>${formatCurrency(total.total_tax)}</strong></span>
                        </div>
                        <div class="stat-row" style="border-top: 2px solid var(--color-primary); padding-top: 8px; margin-top: 4px;">
                            <span class="stat-label" style="color: var(--color-primary); font-weight: 600;">总结余</span>
                            <span class="stat-value" style="color: var(--color-primary); font-weight: 600;"><strong>${formatCurrency(total.total_balance)}</strong></span>
                        </div>
                    </div>
                </div>
            `;
        }

        mobileContainer.innerHTML = html;
        mobileContainer.style.display = 'flex';
    } else {
        // PC端：显示表格，隐藏移动端容器
        if (table) {
            table.style.display = 'table';
        }
        if (mobileContainer) {
            mobileContainer.style.display = 'none';
        }

        const tbody = document.getElementById('statisticsTableBody');
        tbody.innerHTML = '';

        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
            return;
        }

        // 渲染各供应商数据
        items.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.supplier_name}</td>
                <td>${item.order_count}</td>
                <td>${item.product_count}</td>
                <td>${formatCurrency(item.total_internal_price)}</td>
                <td>${formatCurrency(item.total_tax_included_price)}</td>
                <td>${formatCurrency(item.total_service_amount)}</td>
                <td>${formatCurrency(item.total_tax)}</td>
                <td>${formatCurrency(item.total_balance)}</td>
            `;
            tbody.appendChild(row);
        });

        // 渲染总计行
        const totalRow = document.createElement('tr');
        totalRow.className = 'total-row';
        totalRow.innerHTML = `
            <td><strong>${total.supplier_name}</strong></td>
            <td><strong>${total.order_count}</strong></td>
            <td><strong>${total.product_count}</strong></td>
            <td><strong>${formatCurrency(total.total_internal_price)}</strong></td>
            <td><strong>${formatCurrency(total.total_tax_included_price)}</strong></td>
            <td><strong>${formatCurrency(total.total_service_amount)}</strong></td>
            <td><strong>${formatCurrency(total.total_tax)}</strong></td>
            <td><strong>${formatCurrency(total.total_balance)}</strong></td>
        `;
        tbody.appendChild(totalRow);
    }
}

