function Suppliers() {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Поставщики</h1>
        <button className="btn btn-primary">
          <i className="bi bi-plus-circle me-2"></i>
          Добавить поставщика
        </button>
      </div>
      <div className="card">
        <div className="card-body">
          <p className="text-muted">Список поставщиков будет здесь</p>
        </div>
      </div>
    </div>
  )
}

export default Suppliers

