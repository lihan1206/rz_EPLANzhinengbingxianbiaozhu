import { DownloadOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Empty,
  Form,
  InputNumber,
  Table,
  Tag,
  Typography,
  notification,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { analyzeProject, downloadGroupsCsv, getParallelGroups } from '../api/services';
import { ParallelGroup } from '../types';
import { useAppContext } from '../components/AppContext';

export const AnalysisPage = () => {
  const queryClient = useQueryClient();
  const { selectedProjectId } = useAppContext();

  const { data: groups = [], isLoading } = useQuery({
    queryKey: ['groups', selectedProjectId],
    queryFn: () => getParallelGroups(selectedProjectId as number),
    enabled: Boolean(selectedProjectId),
  });

  const analyzeMutation = useMutation({
    mutationFn: ({ projectId, minCount }: { projectId: number; minCount: number }) => analyzeProject(projectId, minCount),
    onSuccess: (data) => {
      notification.success({ message: '分析完成', description: `新生成并线组 ${data.groups_created} 组` });
      queryClient.invalidateQueries({ queryKey: ['groups', selectedProjectId] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      queryClient.invalidateQueries({ queryKey: ['distribution', selectedProjectId] });
    },
    onError: (error: any) => {
      notification.error({
        message: '分析失败',
        description: error?.response?.data?.detail || '请先导入导线数据后重试',
      });
    },
  });

  const columns: ColumnsType<ParallelGroup> = [
    { title: '组名', dataIndex: 'group_name' },
    { title: '数量', dataIndex: 'count' },
    { title: '总截面积(mm²)', dataIndex: 'total_area' },
    { title: '起点', dataIndex: 'start_terminal' },
    { title: '终点', dataIndex: 'end_terminal' },
    {
      title: '并线类型',
      dataIndex: 'parallel_type',
      render: (value: string) => <Tag color="geekblue">{value}</Tag>,
    },
    { title: '智能建议', dataIndex: 'suggestion' },
  ];

  if (!selectedProjectId) {
    return (
      <div className="page-panel">
        <Empty description="请先在顶部选择项目后执行并线分析" />
      </div>
    );
  }

  const handleExport = async () => {
    try {
      const blob = await downloadGroupsCsv(selectedProjectId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `parallel_groups_${selectedProjectId}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      notification.success({ message: '导出成功', description: '并线数据已下载到本地' });
    } catch (error: any) {
      notification.error({
        message: '导出失败',
        description: error?.response?.data?.detail || '请稍后重试',
      });
    }
  };

  return (
    <div className="page-panel">
      <Typography.Title level={4}>智能并线识别与分析</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Form layout="inline" onFinish={(values) => analyzeMutation.mutate({ projectId: selectedProjectId, minCount: values.minCount })}>
          <Form.Item
            label="触发阈值"
            name="minCount"
            initialValue={2}
            rules={[{ required: true, message: '请输入阈值' }]}
          >
            <InputNumber min={2} max={10} addonAfter="根" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={analyzeMutation.isPending}>
              开始分析
            </Button>
          </Form.Item>
          <Form.Item>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              导出并线组CSV
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card>
        <Typography.Title level={5}>并线识别结果</Typography.Title>
        <Table rowKey="id" columns={columns} dataSource={groups} loading={isLoading} pagination={{ pageSize: 8 }} />
      </Card>
    </div>
  );
};
