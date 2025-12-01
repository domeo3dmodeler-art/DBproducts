function Attributes() {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Атрибуты</h1>
        <button className="btn btn-primary">
          <i className="bi bi-plus-circle me-2"></i>
          Добавить атрибут
        </button>
      </div>
      <div className="card">
        <div className="card-body">
          <p className="text-muted">Список атрибутов будет здесь</p>
        </div>
      </div>
    </div>
  )
}

export default Attributes

