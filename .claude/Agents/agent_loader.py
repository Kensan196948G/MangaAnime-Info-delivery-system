#!/usr/bin/env python3
"""
YAML-based Agent Loader
.claude/Agents/*.yamlファイルから動的にエージェントを読み込んで管理
"""

import os
import yaml
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class AgentConfig:
    """エージェント設定データクラス"""
    id: str
    name: str
    version: str
    type: str
    status: str
    priority: int
    description: str
    capabilities: List[str]
    tools: List[str]
    responsibilities: Dict[str, List[str]]
    triggers: Dict[str, List[str]]
    routing_rules: Dict[str, str]
    communication: Dict[str, Any]
    execution: Dict[str, Any]
    monitoring: Dict[str, Any]
    quality_gates: Dict[str, Any]
    collaboration: Dict[str, Any]
    sla: Dict[str, Any]
    configuration: Dict[str, Any]

class AgentLoader:
    """YAMLベースのエージェントローダー"""
    
    def __init__(self, agents_dir: str = None):
        """
        初期化
        
        Args:
            agents_dir: エージェントYAMLファイルのディレクトリパス
        """
        if agents_dir is None:
            agents_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '.'
            )
        self.agents_dir = agents_dir
        self.agents: Dict[str, AgentConfig] = {}
        self.agent_instances: Dict[str, Any] = {}
        
    def load_agent_yaml(self, yaml_file: str) -> Optional[AgentConfig]:
        """
        単一のYAMLファイルからエージェント設定を読み込む
        
        Args:
            yaml_file: YAMLファイルパス
            
        Returns:
            AgentConfig: エージェント設定
        """
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # AgentConfigインスタンスを作成
            agent_config = AgentConfig(
                id=data.get('id'),
                name=data.get('name'),
                version=data.get('version', '1.0.0'),
                type=data.get('type'),
                status=data.get('status', 'active'),
                priority=data.get('priority', 3),
                description=data.get('description', ''),
                capabilities=data.get('capabilities', []),
                tools=data.get('tools', []),
                responsibilities=data.get('responsibilities', {}),
                triggers=data.get('triggers', {}),
                routing_rules=data.get('routing_rules', {}),
                communication=data.get('communication', {}),
                execution=data.get('execution', {}),
                monitoring=data.get('monitoring', {}),
                quality_gates=data.get('quality_gates', {}),
                collaboration=data.get('collaboration', {}),
                sla=data.get('sla', {}),
                configuration=data.get('configuration', {})
            )
            
            print(f"✅ Loaded: {agent_config.id} ({agent_config.name})")
            return agent_config
            
        except Exception as e:
            print(f"❌ Error loading {yaml_file}: {str(e)}")
            return None
    
    def load_all_agents(self) -> Dict[str, AgentConfig]:
        """
        すべてのエージェントYAMLファイルを読み込む
        
        Returns:
            Dict[str, AgentConfig]: エージェントID -> AgentConfigのマッピング
        """
        print(f"\n📂 Loading agents from: {self.agents_dir}")
        print("=" * 60)
        
        yaml_files = [
            f for f in os.listdir(self.agents_dir)
            if f.endswith('.yaml') and f != 'agent-registry.yaml'
        ]
        
        for yaml_file in sorted(yaml_files):
            yaml_path = os.path.join(self.agents_dir, yaml_file)
            agent_config = self.load_agent_yaml(yaml_path)
            
            if agent_config:
                self.agents[agent_config.id] = agent_config
        
        print(f"\n📊 Loaded {len(self.agents)} agents successfully")
        return self.agents
    
    def get_agents_by_type(self, agent_type: str) -> List[AgentConfig]:
        """
        タイプ別にエージェントを取得
        
        Args:
            agent_type: エージェントタイプ
            
        Returns:
            List[AgentConfig]: 該当するエージェントのリスト
        """
        return [
            agent for agent in self.agents.values()
            if agent.type == agent_type
        ]
    
    def get_agents_by_priority(self, priority: int) -> List[AgentConfig]:
        """
        優先度別にエージェントを取得
        
        Args:
            priority: 優先度 (1-3)
            
        Returns:
            List[AgentConfig]: 該当するエージェントのリスト
        """
        return [
            agent for agent in self.agents.values()
            if agent.priority == priority
        ]
    
    def get_agent_for_task(self, task_keywords: List[str]) -> Optional[AgentConfig]:
        """
        タスクキーワードに基づいて最適なエージェントを選択
        
        Args:
            task_keywords: タスクのキーワードリスト
            
        Returns:
            Optional[AgentConfig]: 最適なエージェント
        """
        best_match = None
        max_score = 0
        
        for agent in self.agents.values():
            score = 0
            
            # トリガーキーワードとのマッチング
            if 'keywords' in agent.triggers:
                for keyword in task_keywords:
                    if keyword.lower() in [k.lower() for k in agent.triggers['keywords']]:
                        score += 2
            
            # 能力とのマッチング
            for keyword in task_keywords:
                for capability in agent.capabilities:
                    if keyword.lower() in capability.lower():
                        score += 1
            
            if score > max_score:
                max_score = score
                best_match = agent
        
        return best_match
    
    def get_routing_chain(self, initial_agent_id: str, task_type: str) -> List[str]:
        """
        タスクのルーティングチェーンを取得
        
        Args:
            initial_agent_id: 初期エージェントID
            task_type: タスクタイプ
            
        Returns:
            List[str]: ルーティングチェーン（エージェントIDのリスト）
        """
        chain = [initial_agent_id]
        current_agent = self.agents.get(initial_agent_id)
        
        if not current_agent:
            return chain
        
        # ルーティングルールに基づいてチェーンを構築
        if task_type in current_agent.routing_rules:
            next_agent_id = current_agent.routing_rules[task_type]
            if next_agent_id and next_agent_id not in chain:
                chain.append(next_agent_id)
        
        return chain
    
    def print_agent_summary(self):
        """エージェントサマリーを表示"""
        print("\n" + "=" * 80)
        print("📊 Agent Summary")
        print("=" * 80)
        
        # タイプ別集計
        type_counts = {}
        for agent in self.agents.values():
            type_counts[agent.type] = type_counts.get(agent.type, 0) + 1
        
        print("\n📈 By Type:")
        for agent_type, count in sorted(type_counts.items()):
            print(f"  • {agent_type}: {count} agents")
        
        # 優先度別集計
        priority_counts = {1: 0, 2: 0, 3: 0}
        for agent in self.agents.values():
            priority_counts[agent.priority] = priority_counts.get(agent.priority, 0) + 1
        
        print("\n⚡ By Priority:")
        for priority, count in sorted(priority_counts.items()):
            print(f"  • Priority {priority}: {count} agents")
        
        # ツール使用状況
        tool_usage = {}
        for agent in self.agents.values():
            for tool in agent.tools:
                tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        print("\n🔧 Most Used Tools:")
        for tool, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {tool}: {count} agents")
    
    def export_to_json(self, output_file: str = None):
        """
        エージェント設定をJSONファイルにエクスポート
        
        Args:
            output_file: 出力ファイルパス
        """
        if output_file is None:
            output_file = os.path.join(self.agents_dir, 'agent-registry.json')
        
        registry = {
            'version': '2.0.0',
            'updated_at': datetime.now().isoformat(),
            'agent_count': len(self.agents),
            'agents': {}
        }
        
        for agent_id, agent_config in self.agents.items():
            registry['agents'][agent_id] = asdict(agent_config)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Exported to: {output_file}")
    
    async def initialize_agent(self, agent_id: str) -> bool:
        """
        エージェントを初期化（シミュレーション）
        
        Args:
            agent_id: エージェントID
            
        Returns:
            bool: 初期化成功フラグ
        """
        if agent_id not in self.agents:
            print(f"❌ Agent {agent_id} not found")
            return False
        
        agent = self.agents[agent_id]
        print(f"🚀 Initializing {agent.name}...")
        
        # シミュレート
        await asyncio.sleep(0.1)
        
        self.agent_instances[agent_id] = {
            'config': agent,
            'status': 'running',
            'initialized_at': datetime.now().isoformat()
        }
        
        print(f"✅ {agent.name} initialized")
        return True
    
    async def initialize_all_agents(self):
        """すべてのエージェントを初期化"""
        print("\n" + "=" * 80)
        print("🚀 Initializing All Agents")
        print("=" * 80)
        
        # 優先度順に初期化
        for priority in [1, 2, 3]:
            priority_agents = self.get_agents_by_priority(priority)
            if priority_agents:
                print(f"\n📋 Priority {priority} agents:")
                tasks = [
                    self.initialize_agent(agent.id)
                    for agent in priority_agents
                ]
                await asyncio.gather(*tasks)
        
        print(f"\n✅ All {len(self.agent_instances)} agents initialized")

async def main():
    """メイン処理"""
    # エージェントローダーの初期化
    loader = AgentLoader('/mnt/Linux-ExHDD/WorkFlowAgents/.claude/Agents')
    
    # すべてのエージェントを読み込み
    loader.load_all_agents()
    
    # サマリー表示
    loader.print_agent_summary()
    
    # JSON形式でエクスポート
    loader.export_to_json()
    
    # エージェントの初期化
    await loader.initialize_all_agents()
    
    # タスクマッチングのテスト
    print("\n" + "=" * 80)
    print("🎯 Task Matching Test")
    print("=" * 80)
    
    test_tasks = [
        ['ui', 'design', 'responsive'],
        ['database', 'migration', 'schema'],
        ['payment', 'stripe', 'subscription'],
        ['security', 'vulnerability', 'audit'],
        ['deploy', 'ci', 'pipeline']
    ]
    
    for keywords in test_tasks:
        best_agent = loader.get_agent_for_task(keywords)
        if best_agent:
            print(f"\nTask: {', '.join(keywords)}")
            print(f"  → Best match: {best_agent.name} ({best_agent.id})")
    
    print("\n🎉 Agent loader setup complete!")

if __name__ == "__main__":
    asyncio.run(main())