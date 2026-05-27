export function AdminDashboard() {
  function saveOrder() {
    fetch('/orders', { method: 'POST', body: JSON.stringify({ email }) });
  }

  function exportCsv() {
    window.location.href = '/orders/export';
  }

  return (
    <>
      <button onClick={saveOrder}>Salva ordine</button>
      <button onClick={() => router.push('/reports')}>Apri report</button>
      <button onClick={exportCsv}>Esporta CSV</button>
      <button onClick={() => setFilters(open)}>Filtra ordini</button>
      <RevenueChart data={orders} />
    </>
  );
}

function RevenueChart({ data }) {
  return (
    <LineChart data={data}>
      <XAxis dataKey="month" />
      <YAxis />
      <Tooltip />
    </LineChart>
  );
}
