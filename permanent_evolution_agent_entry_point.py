#!/usr/bin/env python3
"""
Permanent Evolution Agent - Main Entry Point
专属持续进化Agent - 启动即全程闭环，无空档、无闲置。
"""
import sys
import time
from main_loop_controller_orchestrator_system import MainLoopController


def main():
    agent = MainLoopController()
    
    try:
        agent.initialize()
        agent.start()
        
        print("\n" + "="*60)
        print("Permanent Evolution Agent is running...")
        print("Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        while agent.is_running():
            time.sleep(10)
            agent.display_status()
            
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        agent.stop()
        print("\nAgent shutdown complete.")


if __name__ == "__main__":
    main()
