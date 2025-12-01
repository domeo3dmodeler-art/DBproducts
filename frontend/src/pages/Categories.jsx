function Categories() {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Категории</h1>
        <button className="btn btn-primary">
          <i className="bi bi-plus-circle me-2"></i>
          Добавить категорию
        </button>
      </div>
      <div className="card">
        <div className="card-body">
          <p className="text-muted">Список категорий будет здесь</p>
        </div>
      </div>
    </div>
  )
}

export default Categories

