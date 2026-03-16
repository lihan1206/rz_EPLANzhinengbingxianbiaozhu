import React from 'react';
import { Alert, Button, Space } from 'antd';

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends React.Component<React.PropsWithChildren, State> {
  public state: State = { hasError: false };

  public static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error): void {
    // 使用浏览器标准错误通道，避免业务层静默失败
    console.error('页面渲染错误', error);
  }

  public render(): React.ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="page-panel">
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Alert
            message="页面出现异常"
            description="系统已捕获错误，你可以点击下方按钮刷新页面恢复。"
            type="error"
            showIcon
          />
          <Button type="primary" size="large" onClick={() => window.location.reload()}>
            刷新页面
          </Button>
        </Space>
      </div>
    );
  }
}
