import React, { useEffect, useRef, useState } from 'react';
import { Card, Input, Button, Space, Typography, message as antdMessage, Select, Collapse } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, ApartmentOutlined } from '@ant-design/icons';
import { apiService, Graph } from '../services/api';
import './Chat.css';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface ChatMessage {
  role: 'user' | 'assistant';
  // 用户消息文本
  text?: string;
  // 助手结构化内容
  centerEntity?: string;
  answer?: string;
  paths?: string[];
  timestamp: string;
}

const Chat: React.FC = () => {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [selectedGraph, setSelectedGraph] = useState<string | undefined>(undefined);
  const [conversationId, setConversationId] = useState<string>('mock-conv-001');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>('');
  const [sending, setSending] = useState<boolean>(false);
  const messagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchGraphs = async () => {
      try {
        const graphData = await apiService.getGraphs();
        setGraphs(graphData);
        if (graphData.length > 0) {
          setSelectedGraph(graphData[0].id);
        }
      } catch (error) {
        antdMessage.error('获取图谱列表失败');
      }
    };

    fetchGraphs();
  }, []);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed) {
      antdMessage.info('请输入内容');
      return;
    }
    if (!selectedGraph) {
      antdMessage.info('请选择一个图谱');
      return;
    }
    setSending(true);
    const now = new Date().toISOString();
    setMessages((prev) => [...prev, { role: 'user', text: trimmed, timestamp: now }]);
    setInput('');

    try {
      const res = await apiService.chatMock(trimmed, conversationId, selectedGraph);
      setConversationId(res.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          centerEntity: res.center_entity,
          answer: res.answer,
          paths: res.paths ?? [],
          timestamp: res.created_at,
        },
      ]);
    } catch (err) {
      antdMessage.error('发送失败，请检查后端服务是否启动');
    } finally {
      setSending(false);
    }
  };

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages, sending]);

  const renderMarkdown = (md: string): string => {
    try {
      const marked = (window as any).marked;
      const DOMPurify = (window as any).DOMPurify;
      if (marked) {
        const html = marked.parse(md || '');
        return DOMPurify ? DOMPurify.sanitize(html) : html;
      }
      // Fallback：简易换行处理
      return (md || '').replace(/\n/g, '<br/>');
    } catch {
      return (md || '').replace(/\n/g, '<br/>');
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="graph-selector-container">
          <ApartmentOutlined />
          <span className="graph-selector-label">当前图谱:</span>
          <Select
            value={selectedGraph}
            className="graph-selector"
            onChange={setSelectedGraph}
            loading={graphs.length === 0}
            bordered={false}
          >
            {graphs.map((graph) => (
              <Option key={graph.id} value={graph.id}>
                {graph.name}
              </Option>
            ))}
          </Select>
        </div>
      </div>
      <div className="messages" ref={messagesRef}>
        {messages.length === 0 && (
          <div className="empty">开始一条新的消息吧～</div>
        )}

        {messages.map((item, idx) => (
          <div key={idx} className={`message-row ${item.role}`}>
            <div className="avatar">
              {item.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
            </div>
            <div className="content">
              <div className="bubble">
                {item.role === 'assistant' ? (
                  <div className="assistant-content">
                    {item.centerEntity && (
                      <div className="center-entity"><strong>中心实体：</strong>{item.centerEntity}</div>
                    )}
                    {item.answer && (
                      <div
                        className="md-content"
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(item.answer) }}
                      />
                    )}
                    {item.paths && item.paths.length > 0 && (
                      <Collapse ghost>
                        <Collapse.Panel header="推理路径" key="paths">
                          <ul className="paths-list">
                            {item.paths.map((p, i) => (
                              <li key={i}>{p}</li>
                            ))}
                          </ul>
                        </Collapse.Panel>
                      </Collapse>
                    )}
                  </div>
                ) : (
                  <div className="text" style={{ whiteSpace: 'pre-wrap' }}>{item.text}</div>
                )}
              </div>
              <div className="timestamp">
                {new Date(item.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
        ))}

        {sending && (
          <div className="message-row assistant typing">
            <div className="avatar">
              <RobotOutlined />
            </div>
            <div className="content">
              <div className="bubble">
                <span className="dots"><span>.</span><span>.</span><span>.</span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="input-area">
        <TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              if (!sending) sendMessage();
            }
          }}
          autoSize={{ minRows: 1, maxRows: 5 }}
          placeholder="输入消息..."
        />
        <Button type="primary" icon={<SendOutlined />} loading={sending} onClick={sendMessage} />
      </div>
    </div>
  );
};

export default Chat;