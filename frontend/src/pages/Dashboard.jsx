import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { setInteractions, setLoading } from '../store/interactionsSlice';
import api from '../api/axios';
import './Dashboard.css';

const Dashboard = () => {
  const dispatch = useDispatch();
  const { list: interactions, loading } = useSelector((state) => state.interactions);

  useEffect(() => {
    const fetchInteractions = async () => {
      dispatch(setLoading(true));
      try {
        const response = await api.get('/api/interactions');
        dispatch(setInteractions(response.data));
      } catch (err) {
        console.error(err);
      } finally {
        dispatch(setLoading(false));
      }
    };

    fetchInteractions();
  }, [dispatch]);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>CRM Dashboard</h1>
        <Link to="/log-interaction" className="primary-btn">
          + Log New Interaction
        </Link>
      </header>

      <section className="dashboard-content">
        <div className="card full-width">
          <div className="card-header">
            <h2>Recent Interactions</h2>
          </div>
          <div className="card-body">
            {loading ? (
              <p>Loading interactions...</p>
            ) : interactions.length === 0 ? (
              <p>No recent interactions found.</p>
            ) : (
              <table className="interaction-table">
                <thead>
                  <tr>
                    <th>HCP Name</th>
                    <th>Product</th>
                    <th>Sentiment</th>
                    <th>Date</th>
                    <th>Mode</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {interactions.map((item) => (
                    <tr key={item.id}>
                      <td className="bold">{item.hcp_name || 'N/A'}</td>
                      <td>{item.product_discussed || 'N/A'}</td>
                      <td>
                        <span className={`badge sentiment-${(item.sentiment || 'neutral').toLowerCase()}`}>
                          {item.sentiment || 'Neutral'}
                        </span>
                      </td>
                      <td>{item.interaction_date || 'N/A'}</td>
                      <td>{item.mode || 'N/A'}</td>
                      <td>
                        <span className={`badge status-${(item.status || 'completed').toLowerCase()}`}>
                          {item.status || 'Completed'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
