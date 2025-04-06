import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";

export default function Home() {
  // State management
  const [salesReps, setSalesReps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useState({
    name: "",
    role: "",
    region: "",
    skills: "",
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [expandedSalesRep, setExpandedSalesRep] = useState(null);

  // AI Assistant state
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  // Load sales representatives data
  useEffect(() => {
    fetchData();
  }, [currentPage, pageSize]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Build query parameters
      const queryParams = new URLSearchParams();
      queryParams.append("page", currentPage);
      queryParams.append("page_size", pageSize);

      // Add individual search parameters if they exist
      if (searchParams.name) queryParams.append("name", searchParams.name);
      if (searchParams.role) queryParams.append("role", searchParams.role);
      if (searchParams.region)
        queryParams.append("region", searchParams.region);
      if (searchParams.skills)
        queryParams.append("skills", searchParams.skills);

      const response = await fetch(
        `http://localhost:8000/api/sales-reps?${queryParams.toString()}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch data");
      }

      const result = await response.json();
      setSalesReps(result.data || []);
      setTotalPages(result.meta?.total_pages || 1);
      setTotalItems(result.meta?.total_items || 0);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  // Handle AI Assistant question submission
  const handleAiSubmit = async (e) => {
    e.preventDefault();

    if (!aiQuestion.trim()) return;

    setAiLoading(true);
    setAiResponse("");

    try {
      const response = await fetch("http://localhost:8000/api/ai", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: aiQuestion,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get AI response");
      }

      const result = await response.json();
      setAiResponse(result.answer);
    } catch (error) {
      console.error("Error getting AI response:", error);
      setAiResponse(
        "Maaf, terjadi kesalahan saat berkomunikasi dengan asisten AI. Silakan coba lagi nanti."
      );
    } finally {
      setAiLoading(false);
    }
  };

  // Handle search input changes
  const handleSearchChange = (e, field) => {
    setSearchParams({
      ...searchParams,
      [field]: e.target.value,
    });
  };

  // Handle search form submission
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setCurrentPage(1); // Reset to first page on new search
    fetchData();
  };

  // Clear all search fields
  const handleClearSearch = () => {
    setSearchParams({
      name: "",
      role: "",
      region: "",
      skills: "",
    });
    setTimeout(() => {
      fetchData();
    }, 0);
  };

  // Handle pagination
  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // Handle row expansion to show deals and clients
  const handleExpandRow = (id) => {
    if (expandedSalesRep === id) {
      setExpandedSalesRep(null); // Toggle off if the same row is clicked
    } else {
      setExpandedSalesRep(id); // Expand the clicked row
    }
  };

  return (
    <div>
      {/* Header */}
      <header className="header">
        <div className="container">
          <div className="header-content">
            <h1 className="header-title">Sales Dashboard</h1>
          </div>
        </div>
      </header>

      <main className="container main-content">
        {/* AI Assistant */}
        <div className="ai-assistant">
          <div className="ai-assistant-header">
            <div className="ai-assistant-icon">
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 16v-4"></path>
                <path d="M12 8h.01"></path>
              </svg>
            </div>
            <h2 className="ai-assistant-title">AI Assistant</h2>
          </div>

          <form onSubmit={handleAiSubmit} className="ai-assistant-form">
            <input
              type="text"
              value={aiQuestion}
              onChange={(e) => setAiQuestion(e.target.value)}
              placeholder="Ask about sales representatives..."
              className="ai-assistant-input"
              disabled={aiLoading}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={aiLoading || !aiQuestion.trim()}
            >
              Ask
            </button>
          </form>

          {aiLoading && (
            <div className="ai-assistant-loading">
              <div className="spinner"></div>
              <span>Memproses pertanyaan...</span>
            </div>
          )}

          {aiResponse && !aiLoading && (
            <div className="ai-assistant-response">{aiResponse}</div>
          )}
        </div>

        {/* Table container with integrated search */}
        <div className="table-container">
          {/* Search area directly above table */}
          <div className="search-area">
            <form onSubmit={handleSearchSubmit} className="search-form">
              <div className="search-form-inputs">
                <div className="search-input-group">
                  <label htmlFor="nameSearch">Name</label>
                  <input
                    id="nameSearch"
                    type="text"
                    placeholder="Search by name"
                    value={searchParams.name}
                    onChange={(e) => handleSearchChange(e, "name")}
                    className="filter-input"
                  />
                </div>

                <div className="search-input-group">
                  <label htmlFor="roleSearch">Role</label>
                  <input
                    id="roleSearch"
                    type="text"
                    placeholder="Search by role"
                    value={searchParams.role}
                    onChange={(e) => handleSearchChange(e, "role")}
                    className="filter-input"
                  />
                </div>

                <div className="search-input-group">
                  <label htmlFor="regionSearch">Region</label>
                  <select
                    id="regionSearch"
                    value={searchParams.region}
                    onChange={(e) => handleSearchChange(e, "region")}
                    className="filter-input"
                  >
                    <option value="">All Regions</option>
                    <option value="North America">North America</option>
                    <option value="Europe">Europe</option>
                    <option value="Asia-Pacific">Asia-Pacific</option>
                    <option value="South America">South America</option>
                    <option value="Middle East">Middle East</option>
                  </select>
                </div>

                <div className="search-input-group">
                  <label htmlFor="skillsSearch">Skills</label>
                  <input
                    id="skillsSearch"
                    type="text"
                    placeholder="Search by skills"
                    value={searchParams.skills}
                    onChange={(e) => handleSearchChange(e, "skills")}
                    className="filter-input"
                  />
                </div>
              </div>

              <div className="search-form-buttons">
                <button type="submit" className="btn btn-primary">
                  Search
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleClearSearch}
                >
                  Clear
                </button>
              </div>
            </form>
          </div>

          {/* Table */}
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Role</th>
                <th>Region</th>
                <th>Skills</th>
                <th style={{ textAlign: "center" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: "center" }}>
                    <div style={{ display: "flex", justifyContent: "center" }}>
                      <div className="spinner"></div>
                    </div>
                  </td>
                </tr>
              ) : salesReps.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: "center" }}>
                    No sales representatives found
                  </td>
                </tr>
              ) : (
                salesReps.map((rep) => (
                  <>
                    <tr
                      key={rep.id}
                      className={
                        expandedSalesRep === rep.id ? "expanded-row" : ""
                      }
                    >
                      <td>{rep.name || "N/A"}</td>
                      <td>{rep.role || "N/A"}</td>
                      <td>{rep.region || "N/A"}</td>
                      <td>
                        <div className="skills-container">
                          {rep.skills &&
                            rep.skills.map((skill, index) => (
                              <span key={index} className="skill-badge">
                                {skill}
                              </span>
                            ))}
                        </div>
                      </td>
                      <td>
                        <div className="actions">
                          <button
                            className="action-btn view"
                            onClick={() => handleExpandRow(rep.id)}
                            aria-label={
                              expandedSalesRep === rep.id
                                ? "Hide details"
                                : "Show details"
                            }
                          >
                            <svg
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                              />
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                              />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>

                    {/* Expanded row to show deals and clients */}
                    {expandedSalesRep === rep.id && (
                      <tr className="details-row">
                        <td colSpan="5">
                          <div className="details-container">
                            <div className="details-section">
                              <h3>Deals</h3>
                              <table className="inner-table">
                                <thead>
                                  <tr>
                                    <th>Client</th>
                                    <th>Value</th>
                                    <th>Status</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {rep.deals &&
                                    rep.deals.map((deal, index) => (
                                      <tr key={index}>
                                        <td>{deal.client}</td>
                                        <td>${deal.value.toLocaleString()}</td>
                                        <td>
                                          <span
                                            className={`status-badge ${
                                              deal.status === "Closed Won"
                                                ? "status-active"
                                                : deal.status === "In Progress"
                                                ? "status-pending"
                                                : "status-default"
                                            }`}
                                          >
                                            {deal.status}
                                          </span>
                                        </td>
                                      </tr>
                                    ))}
                                </tbody>
                              </table>
                            </div>

                            <div className="details-section">
                              <h3>Clients</h3>
                              <table className="inner-table">
                                <thead>
                                  <tr>
                                    <th>Name</th>
                                    <th>Industry</th>
                                    <th>Contact</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {rep.clients &&
                                    rep.clients.map((client, index) => (
                                      <tr key={index}>
                                        <td>{client.name}</td>
                                        <td>{client.industry}</td>
                                        <td>{client.contact}</td>
                                      </tr>
                                    ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))
              )}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="pagination">
            <div className="pagination-info">
              Page <span style={{ fontWeight: 500 }}>{currentPage}</span> of{" "}
              <span style={{ fontWeight: 500 }}>{totalPages}</span>
            </div>
            <div className="pagination-buttons">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="page-btn"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
              {[...Array(totalPages)].map((_, i) => (
                <button
                  key={i + 1}
                  onClick={() => handlePageChange(i + 1)}
                  className={`page-btn ${
                    currentPage === i + 1 ? "active" : ""
                  }`}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="page-btn"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
