import { InboxOutlined } from '@ant-design/icons';
import { Button, Card, Empty, Space, Table, Typography, Upload, notification } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { getImportRecords, importEplan } from '../api/services';
import { ImportRecord } from '../types';
import { useAppContext } from '../components/AppContext';

export const ImportPage = () => {
  const queryClient = useQueryClient();
  const { selectedProjectId } = useAppContext();
  const [fileList, setFileList] = useState<File[]>([]);

  const { data: records = [], isLoading } = useQuery({
    queryKey: ['import-records', selectedProjectId],
    queryFn: () => getImportRecords(selectedProjectId as number),
    enabled: Boolean(selectedProjectId),
  });

  const importMutation = useMutation({
    mutationFn: ({ projectId, file }: { projectId: number; file: File }) => importEplan(projectId, file),
    onSuccess: (data) => {
      notification.success({
        message: '导入成功',
        description: `导入导线 ${data.imported_wires} 条，元件 ${data.imported_components} 个`,
      });
      setFileList([]);
      queryClient.invalidateQueries({ queryKey: ['import-records', selectedProjectId] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
    onError: (error: any) => {
      notification.error({
        message: '导入失败',
        description: error?.response?.data?.detail || '请检查文件格式，支持 CSV/XML',
      });
    },
  });

  const columns: ColumnsType<ImportRecord> = [
    { title: '文件名', dataIndex: 'filename' },
    { title: '格式', dataIndex: 'file_format' },
    { title: '记录数', dataIndex: 'row_count' },
    { title: '状态', dataIndex: 'status' },
    {
      title: '导入时间',
      dataIndex: 'created_at',
      render: (value: string) => new Date(value).toLocaleString('zh-CN'),
    },
  ];

  if (!selectedProjectId) {
    return (
      <div className="page-panel">
        <Empty description="请先在顶部选择项目后再导入数据" />
      </div>
    );
  }

  return (
    <div className="page-panel">
      <Typography.Title level={4}>EPLAN 数据导入</Typography.Title>
      <Card style={{ marginBottom: 16 }}>
        <Upload.Dragger
          accept=".csv,.xml"
          multiple={false}
          beforeUpload={(file) => {
            setFileList([file]);
            return false;
          }}
          fileList={fileList as any}
          onRemove={() => {
            setFileList([]);
            return true;
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">支持 CSV/XML，导入后将写入数据库并保留版本记录</p>
        </Upload.Dragger>
        <Space style={{ marginTop: 12 }}>
          <Button
            type="primary"
            disabled={fileList.length === 0}
            loading={importMutation.isPending}
            onClick={() => {
              if (!selectedProjectId || fileList.length === 0) return;
              importMutation.mutate({ projectId: selectedProjectId, file: fileList[0] });
            }}
          >
            开始导入
          </Button>
        </Space>
      </Card>

      <Card>
        <Typography.Title level={5}>导入历史</Typography.Title>
        <Table rowKey="id" columns={columns} dataSource={records} loading={isLoading} pagination={false} />
      </Card>
    </div>
  );
};
