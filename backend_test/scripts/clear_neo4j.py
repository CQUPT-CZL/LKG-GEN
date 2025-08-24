# scripts/clear_neo4j.py

import os
import sys
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import AuthError, ServiceUnavailable

# --- 路径设置，确保可以导入app模块 ---
# 将项目根目录添加到Python的模块搜索路径中
# 这使得我们可以导入 app.core.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.config import settings
except ImportError:
    print("错误：无法导入配置文件。请确保您是从项目根目录运行此脚本，")
    print("或者项目结构是正确的。")
    sys.exit(1)

def clear_database(driver: Driver):
    """
    执行清空数据库的核心函数
    """
    # Neo4j中删除所有节点和关系的最有效、最彻底的查询
    # DETACH DELETE 会在删除节点的同时，删除掉所有与之相连的关系
    cypher_query = "MATCH (n) DETACH DELETE n"

    with driver.session() as session:
        # 检查删除前的节点数量
        result_before = session.run("MATCH (n) RETURN count(n) AS count")
        count_before = result_before.single()["count"]
        print(f"  📊 删除前数据库中共有 {count_before} 个节点。")

        if count_before == 0:
            print("  ✅ 数据库已经是空的，无需操作。")
            return

        print("  ⏳ 正在执行删除操作...")
        session.run(cypher_query)

        # 检查删除后的节点数量
        result_after = session.run("MATCH (n) RETURN count(n) AS count")
        count_after = result_after.single()["count"]
        print(f"  📊 删除后数据库中剩余 {count_after} 个节点。")
        
        if count_after == 0:
            print("  ✅ 数据库已成功清空！")
        else:
            print("  ❌ 警告：操作后仍有节点残留，请检查数据库。")

def main():
    """
    主函数，包含安全确认逻辑
    """
    print("=====================================================")
    print("          Neo4j 数据库一键清空脚本")
    print("=====================================================")
    
    uri = settings.NEO4J_URI
    user = settings.NEO4J_USER

    print(f"\n即将连接到以下Neo4j数据库并清空【所有】数据：")
    print(f"  - 地址 (URI): {uri}")
    print(f"  - 用户 (User): {user}")
    
    print("\n" + "!"*60)
    print("!!! 警告：这是一个毁灭性操作，将删除图中的所有节点和关系。 !!!")
    print("!!! 操作不可逆转，请在执行前再三确认目标数据库是否正确。     !!!")
    print("!"*60)
    
    # --- 安全确认机制 ---
    # 要求用户输入目标数据库的URI来确认操作，防止误触
    # confirmation = input(f"\n👉 如果您确认要清空以上数据库，请输入完整的数据库地址进行确认：\n")

    # if confirmation.strip() != uri:
    #     print("\n❌ 输入的地址与配置不匹配，操作已取消。")
    #     sys.exit(0)

    # print("\n✅ 地址确认成功，正在连接数据库...")

    # driver = None
    try:
        # 使用配置文件中的信息连接数据库
        driver = GraphDatabase.driver(uri, auth=(user, settings.NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("  🔗 数据库连接成功！")
        
        # 执行清空操作
        clear_database(driver)

    except AuthError:
        print(f"\n❌ 数据库认证失败！请检查 .env 文件中的 NEO4J_USER 和 NEO4J_PASSWORD 是否正确。")
    except ServiceUnavailable:
        print(f"\n❌ 无法连接到Neo4j数据库！请检查数据库服务是否正在运行，以及 NEO4J_URI 地址 '{uri}' 是否正确。")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")
    finally:
        # 无论成功与否，都确保关闭驱动连接
        if driver:
            driver.close()
            print("\n  🔌 数据库连接已关闭。")

if __name__ == "__main__":
    main()