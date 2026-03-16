import { Alert, Card, Col, Row, Skeleton, Table, Tabs, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useQuery } from '@tanstack/react-query';

import { getLogs, getUsers } from '../api/services';
import { OperationLog, UserInfo } from '../types';

export const UsersPage = () => {
  const usersQuery = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
    retry: false,
  });

  const logsQuery = useQuery({
    queryKey: ['logs'],
    queryFn: getLogs,
    retry: false,
  });

  const isForbidden =
    usersQuery.error && (usersQuery.error as any)?.response?.status === 403;

  if (isForbidden) {
    return (
      <div className="page-panel">
        <Alert type="warning" showIcon message="权限不足" description="仅管理员可查看用户与操作日志" />
      </div>
    );
  }

  const userColumns: ColumnsType<UserInfo> = [
    { title: '用户名', dataIndex: 'username' },
    { title: '角色', dataIndex: 'role' },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      render: (value: string) => new Date(value).toLocaleString('zh-CN'),
    },
  ];

  const logColumns: ColumnsType<OperationLog> = [
    { title: '动作', dataIndex: 'action' },
    { title: '目标', dataIndex: 'target' },
    { title: '详情', dataIndex: 'detail' },
    {
      title: '时间',
      dataIndex: 'created_at',
      render: (value: string) => new Date(value).toLocaleString('zh-CN'),
    },
  ];

  return (
    <div className="page-panel">
      <Typography.Title level={4}>用户与权限控制</Typography.Title>
      {usersQuery.isLoading || logsQuery.isLoading ? (
        <Skeleton active />
      ) : (
        <Row gutter={16}>
          <Col span={24}>
            <Card>
              <Tabs
                items={[
                  {
                    key: 'users',
                    label: '用户列表',
                    children: (
                      <Table
                        rowKey="id"
                        columns={userColumns}
                        dataSource={usersQuery.data || []}
                        pagination={false}
                      />
                    ),
                  },
                  {
                    key: 'logs',
                    label: '操作日志',
                    children: (
                      <Table
                        rowKey="id"
                        columns={logColumns}
                        dataSource={logsQuery.data || []}
                        pagination={{ pageSize: 10 }}
                      />
                    ),
                  },
                ]}
              />
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};
