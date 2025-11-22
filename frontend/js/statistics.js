/**
 * 统计信息功能
 */

// 加载统计信息
async function loadStatistics() {
    try {
        const response = await apiRequest('/statistics/');
        renderStatisticsTable(response.items, response.total);
    } catch (error) {
        showMessage('加载统计信息失败: ' + error.message, 'error');
    }
}

// 渲染统计表格
function renderStatisticsTable(items, total) {
    const tbody = document.getElementById('statisticsTableBody');
    tbody.innerHTML = '';
    
    if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }
    
    // 渲染各厂家数据
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

