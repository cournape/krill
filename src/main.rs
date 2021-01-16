use std::error;
use std::io::{Stdout, stdout, Write};

use std::thread;
use std::time::Duration;

use tui::Terminal;
use tui::backend::CrosstermBackend;
use crossterm::{
    event::{EnableMouseCapture, DisableMouseCapture},
    execute,
    terminal::{enable_raw_mode, disable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};


fn initialize_terminal(stdout: &mut Stdout) -> Result<Terminal<CrosstermBackend<&mut Stdout>>, Box<dyn error::Error>> {
    enable_raw_mode()?;
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;

    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    terminal.hide_cursor()?;

    Ok(terminal)
}

fn deinit_terminal(terminal: &mut Terminal<CrosstermBackend<&mut Stdout>>) -> Result<(), Box<dyn error::Error>> {
    terminal.show_cursor()?;

    let mut stdout = stdout();
    execute!(stdout, DisableMouseCapture, LeaveAlternateScreen)?;
    disable_raw_mode()?;

    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut stdout = stdout();
    let mut terminal = initialize_terminal(&mut stdout)?;

    thread::sleep(Duration::from_millis(1000));

    deinit_terminal(&mut terminal)?;

    Ok(())
}
