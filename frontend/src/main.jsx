import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './styles.css';

class ErrorBoundary extends React.Component {
  constructor(props) {super(props); this.state = {failed: false};}
  static getDerivedStateFromError() {return {failed: true};}
  render() {
    return this.state.failed ? <main><h1>The workspace could not be displayed.</h1><p>Refresh the page and inspect the backend terminal. No automatic API retry is made.</p></main> : this.props.children;
  }
}
createRoot(document.getElementById('root')).render(<ErrorBoundary><App /></ErrorBoundary>);
