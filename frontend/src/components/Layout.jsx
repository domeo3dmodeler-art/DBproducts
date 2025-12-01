import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  return (
    <div className="d-flex flex-column" style={{ minHeight: '100vh' }}>
      <nav className="navbar navbar-expand-lg navbar-light bg-white border-bottom">
        <div className="container-fluid">
          <Link className="navbar-brand" to="/">
            <i className="bi bi-box-seam-fill text-primary me-2"></i>
            Управление товарами
          </Link>
          <button
            className="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarNav"
          >
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto">
              <li className="nav-item">
                <Link
                  className={`nav-link ${isActive('/') ? 'active' : ''}`}
                  to="/"
                >
                  <i className="bi bi-house-door me-1"></i>
                  Главная
                </Link>
              </li>
              <li className="nav-item">
                <Link
                  className={`nav-link ${isActive('/products') ? 'active' : ''}`}
                  to="/products"
                >
                  <i className="bi bi-box me-1"></i>
                  Товары
                </Link>
              </li>
              <li className="nav-item">
                <Link
                  className={`nav-link ${isActive('/import') ? 'active' : ''}`}
                  to="/import"
                >
                  <i className="bi bi-upload me-1"></i>
                  Импорт
                </Link>
              </li>
              <li className="nav-item dropdown">
                <a
                  className={`nav-link dropdown-toggle ${
                    ['/categories', '/suppliers', '/subcategories', '/attributes'].some((p) =>
                      isActive(p)
                    )
                      ? 'active'
                      : ''
                  }`}
                  href="#"
                  role="button"
                  data-bs-toggle="dropdown"
                >
                  <i className="bi bi-gear me-1"></i>
                  Настройки
                </a>
                <ul className="dropdown-menu">
                  <li>
                    <Link className="dropdown-item" to="/categories">
                      <i className="bi bi-folder me-2"></i>
                      Категории
                    </Link>
                  </li>
                  <li>
                    <Link className="dropdown-item" to="/suppliers">
                      <i className="bi bi-building me-2"></i>
                      Поставщики
                    </Link>
                  </li>
                  <li>
                    <Link className="dropdown-item" to="/subcategories">
                      <i className="bi bi-tags me-2"></i>
                      Подкатегории
                    </Link>
                  </li>
                  <li>
                    <hr className="dropdown-divider" />
                  </li>
                  <li>
                    <Link className="dropdown-item" to="/attributes">
                      <i className="bi bi-list-check me-2"></i>
                      Атрибуты
                    </Link>
                  </li>
                </ul>
              </li>
            </ul>
            <ul className="navbar-nav">
              <li className="nav-item dropdown">
                <a
                  className="nav-link dropdown-toggle"
                  href="#"
                  role="button"
                  data-bs-toggle="dropdown"
                >
                  <i className="bi bi-person-circle me-1"></i>
                  {user?.username || 'Пользователь'}
                </a>
                <ul className="dropdown-menu dropdown-menu-end">
                  <li>
                    <button className="dropdown-item" onClick={logout}>
                      <i className="bi bi-box-arrow-right me-2"></i>
                      Выход
                    </button>
                  </li>
                </ul>
              </li>
            </ul>
          </div>
        </div>
      </nav>

      <main className="container-fluid mt-4 flex-grow-1">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

