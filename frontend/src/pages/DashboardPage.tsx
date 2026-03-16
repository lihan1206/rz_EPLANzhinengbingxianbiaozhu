import { Card, Col, Empty, Row, Skeleton, Statistic, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import ReactECharts from 'echarts-for-react';

import { getDashboardSummary, getDistribution } from '../api/services';
import { useAppContext } from '../components/AppContext';

export const DashboardPage = () => {
  const { selectedProjectId } = useAppContext();
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: getDashboardSummary,
  });

  const { data: distribution = [], isLoading: distributionLoading } = useQuery({
    queryKey: ['distribution', selectedProjectId],
    queryFn: () => getDistribution(selectedProjectId as number),
    enabled: Boolean(selectedProjectId),
  });

  return (
    <div className="page-panel">
      <Typography.Title level={4}>系统总览</Typography.Title>
      {summaryLoading || !summary ? (
        <Skeleton active />
      ) : (
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12} xl={6}>
            <Card>
              <Statistic title="项目总数" value={summary.project_count} />
            </Card>
          </Col>
          <Col xs={24} md={12} xl={6}>
            <Card>
              <Statistic title="导线总数" value={summary.wire_count} />
            </Card>
          </Col>
          <Col xs={24} md={12} xl={6}>
            <Card>
              <Statistic title="并线组数" value={summary.parallel_group_count} />
            </Card>
          </Col>
          <Col xs={24} md={12} xl={6}>
            <Card>
              <Statistic title="标注总数" value={summary.annotation_count} />
            </Card>
          </Col>
        </Row>
      )}

      <Card style={{ marginTop: 20 }}>
        <Typography.Title level={5}>并线类型分布</Typography.Title>
        {!selectedProjectId ? (
          <Empty description="请先在顶部选择项目" />
        ) : distributionLoading ? (
          <Skeleton active />
        ) : (
          <ReactECharts
            style={{ height: 360 }}
            option={{
              tooltip: { trigger: 'item' },
              legend: { top: 'bottom' },
              series: [
                {
                  name: '并线类型',
                  type: 'pie',
                  radius: ['35%', '68%'],
                  data: distribution,
                },
              ],
            }}
          />
        )}
      </Card>
    </div>
  );
};
