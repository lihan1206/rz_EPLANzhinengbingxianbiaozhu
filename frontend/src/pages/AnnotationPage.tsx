import { Button, Card, Empty, Form, Input, Table, Typography, notification } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { generateAnnotations, getAnnotations } from '../api/services';
import { Annotation } from '../types';
import { useAppContext } from '../components/AppContext';

export const AnnotationPage = () => {
  const queryClient = useQueryClient();
  const { selectedProjectId } = useAppContext();

  const { data: annotations = [], isLoading } = useQuery({
    queryKey: ['annotations', selectedProjectId],
    queryFn: () => getAnnotations(selectedProjectId as number),
    enabled: Boolean(selectedProjectId),
  });

  const generateMutation = useMutation({
    mutationFn: ({ projectId, template, style }: { projectId: number; template: string; style: string }) =>
      generateAnnotations(projectId, template, style),
    onSuccess: (data) => {
      notification.success({ message: '标注生成成功', description: `本次生成 ${data.length} 条标注` });
      queryClient.invalidateQueries({ queryKey: ['annotations', selectedProjectId] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
    onError: (error: any) => {
      notification.error({
        message: '生成失败',
        description: error?.response?.data?.detail || '请先完成并线分析',
      });
    },
  });

  const columns: ColumnsType<Annotation> = [
    { title: '标注内容', dataIndex: 'text' },
    { title: '样式', dataIndex: 'style' },
    {
      title: '坐标',
      render: (_, row) => `(${row.position_x}, ${row.position_y})`,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      render: (value: string) => new Date(value).toLocaleString('zh-CN'),
    },
  ];

  if (!selectedProjectId) {
    return (
      <div className="page-panel">
        <Empty description="请先在顶部选择项目后生成标注" />
      </div>
    );
  }

  return (
    <div className="page-panel">
      <Typography.Title level={4}>自动标注生成</Typography.Title>
      <Card style={{ marginBottom: 16 }}>
        <Form
          layout="inline"
          onFinish={(values) =>
            generateMutation.mutate({
              projectId: selectedProjectId,
              template: values.template,
              style: values.style,
            })
          }
        >
          <Form.Item
            label="标注模板"
            name="template"
            initialValue="{{count}}x{{area}}mm²"
            rules={[{ required: true, message: '请输入模板' }]}
          >
            <Input style={{ width: 280 }} placeholder="支持 {{count}} 与 {{area}}" />
          </Form.Item>
          <Form.Item label="标注风格" name="style" initialValue="标准">
            <Input style={{ width: 160 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={generateMutation.isPending}>
              批量生成
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card>
        <Typography.Title level={5}>标注结果列表</Typography.Title>
        <Table rowKey="id" columns={columns} dataSource={annotations} loading={isLoading} pagination={{ pageSize: 8 }} />
      </Card>
    </div>
  );
};
