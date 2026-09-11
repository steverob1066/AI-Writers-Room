"""Contract every feature tab follows so main.py can discover and load tabs generically.

To add a new feature: drop a new file in tabs/, define a class named `Tab(BaseTab)`,
implement build(). It will appear in the GUI automatically -- no changes to main.py needed.
"""
from abc import ABC, abstractmethod
import customtkinter as ctk


class BaseTab(ABC):
    tab_id: str = "base"       # stable key used for settings storage -- don't rename once in use
    tab_title: str = "Base"    # label shown on the tab

    def __init__(self, parent: ctk.CTkFrame):
        self.parent = parent

    @abstractmethod
    def build(self) -> None:
        """Build this tab's widgets inside self.parent. Called once at startup."""
        raise NotImplementedError
