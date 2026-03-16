import { ExclamationCircleFilled, PlusOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Space,
  Table,
  Tag,
  Typography,
  notification,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { createProject, deleteProject, getProjects } from '../api/services';
import { Project } from '../types';
import { useAppContext } from '../components/AppContext';

export const ProjectsPage = () => {
  const queryClient = useQueryClient();
  const { selectedProjectId, setSelectedProjectId } = useAppContext();
  const [modalOpen, setModalOpen] = useState(false);

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      notification.success({ message: '项目创建成功', description: `已创建 ${project.name}` });
      setSelectedProjectId(project.id);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'layout'] });
      setModalOpen(false);
    },
    onError: (error: any) => {
      notification.error({
        message: '创建失败',
        description: error?.response?.data?.detail || '请检查输入后重试',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      notification.success({ message: '项目删除成功' });
      setSelectedProjectId(undefined);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'layout'] });
    },
    onError: (error: any) => {
      notification.error({
        message: '删除失败',
        description: error?.response?.data?.detail || '删除操作未完成',
      });
    },
  });

  const [form] = Form.useForm<{ name: string; version: string }>();

  const columns: ColumnsType<Project> = [
    { title: '项目名称', dataIndex: 'name' },
    { title: '版本', dataIndex: 'version', render: (value) => <Tag color="blue">{value}</Tag> },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      render: (value: string) => new Date(value).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          <Button
            type={selectedProjectId === record.id ? 'primary' : 'default'}
            onClick={() => setSelectedProjectId(record.id)}
          >
            {selectedProjectId === record.id ? '当前项目' : '设为当前'}
          </Button>
          <Button
            danger
            onClick={() => {
              Modal.confirm({
                title: `确认删除项目「${record.name}」吗？`,
                icon: <ExclamationCircleFilled style={{ color: '#d4380d' }} />,
                content: (
                  <Card bordered={false} style={{ background: '#fff2f0', marginTop: 8 }}>
                    删除后将清空该项目的导入记录、并线分析结果和标注结果，此操作不可撤销。
                  </Card>
                ),
                okText: '确认删除',
                okButtonProps: { danger: true },
                cancelText: '取消',
                onOk: () => deleteMutation.mutate(record.id),
              });
            }}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-panel">
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          项目管理
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新建项目
        </Button>
      </Space>

      <Table rowKey="id" columns={columns} dataSource={projects} loading={isLoading} pagination={false} />

      <Modal
        title="新建项目"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        okText="创建"
        cancelText="取消"
        confirmLoading={createMutation.isPending}
        onOk={() => {
          form
            .validateFields()
            .then((values) => createMutation.mutate(values))
            .catch(() => undefined);
        }}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="项目名称" name="name" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="例如：主控柜一次回路" maxLength={100} />
          </Form.Item>
          <Form.Item label="版本号" name="version" rules={[{ required: true, message: '请输入版本号' }]}>
            <Input placeholder="例如：v2" maxLength={20} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
