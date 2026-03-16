import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { App } from './App';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AppContextProvider } from './components/AppContext';
import './styles.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 20000,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#0d7c91',
          borderRadius: 12,
          fontFamily: '"Noto Sans SC", "HarmonyOS Sans SC", "PingFang SC", sans-serif',
        },
      }}
    >
      <AntApp>
        <QueryClientProvider client={queryClient}>
          <ErrorBoundary>
            <AppContextProvider>
              <App />
            </AppContextProvider>
          </ErrorBoundary>
        </QueryClientProvider>
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>,
);
