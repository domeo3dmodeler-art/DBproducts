import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'

function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/api/dashboard/stats')
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Загрузка...</span>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="mb-4">Главная страница</h1>

      <div className="row g-4 mb-4">
        <div className="col-md-3">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title text-muted small">Категории</h5>
              <h2 className="mb-0">{stats?.categories_count || 0}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title text-muted small">Поставщики</h5>
              <h2 className="mb-0">{stats?.suppliers_count || 0}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title text-muted small">Подкатегории</h5>
              <h2 className="mb-0">{stats?.subcategories_count || 0}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title text-muted small">Товары</h5>
              <h2 className="mb-0">{stats?.products_count || 0}</h2>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h5 className="mb-0">Статистика по статусам товаров</h5>
        </div>
        <div className="card-body">
          {stats?.status_stats ? (
            <div className="row">
              {Object.entries(stats.status_stats).map(([status, count]) => (
                <div key={status} className="col-md-2 mb-3">
                  <div className="text-center">
                    <div className="fs-4 fw-bold">{count}</div>
                    <div className="text-muted small">{status}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">Нет данных</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard

